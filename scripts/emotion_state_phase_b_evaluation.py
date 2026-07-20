from __future__ import annotations

import csv
import copy
import hashlib
import io
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Collection, Iterator, Mapping, Sequence
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
    validate_config,
    validate_decision_inputs,
    validate_environment_lock,
    validate_evaluation_result,
    validate_feature_schema,
    validate_fit_inputs,
    validate_labels_and_actors,
    validate_payload_self_hash,
    validate_partition_role,
    validate_probability_inputs,
    validate_provenance_payload,
    validate_split_schema,
    canonical_payload_sha256,
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


def _canonical_sha256(value: Any) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest().upper()


def _array_commitment(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    metadata = json.dumps(
        {
            "dtype": contiguous.dtype.str,
            "shape": list(contiguous.shape),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(
        metadata + b"\0" + contiguous.tobytes(order="C")
    ).hexdigest().upper()


def frozen_model_identity(seed: int) -> dict[str, Any]:
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError("model seed must be a 32-bit non-negative integer")
    classifier = {
        "C": 1.0,
        "class_weight": None,
        "solver": "lbfgs",
        "max_iter": 10000,
        "random_state": seed,
        "l1_ratio": 0.0,
        "multiclass_semantics": "six_class_multinomial_softmax",
    }
    return {
        "schema_id": "emotion-state-phase-b-frozen-model-identity-v1",
        "model_order": list(MODEL_KEYS),
        "class_order": list(CLASS_ORDER),
        "class_prior": {"strategy": "prior"},
        "sentence_id": {
            "steps": ["one_hot", "classifier"],
            "one_hot_handle_unknown": "ignore",
            "classifier": dict(classifier),
        },
        "acoustic": {
            "steps": ["standardize", "classifier"],
            "standardizer": "StandardScaler",
            "classifier": dict(classifier),
        },
    }


@dataclass(frozen=True, init=False)
class ValidatedSplitAssignment:
    _records: tuple[CremaLabelRecord, ...]
    _assignment: tuple[tuple[str, str], ...]
    _seed_digest: str
    _manifest_sha256: str

    def __init__(self, *_: Any, **__: Any) -> None:
        raise TypeError("validated split assignments are minted after validation")


def _validate_split_assignment_components(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
    seed_digest: str,
) -> tuple[
    tuple[CremaLabelRecord, ...],
    tuple[tuple[str, str], ...],
    str,
]:
    from scripts.emotion_state_phase_b_splits import (
        build_actor_split,
        split_manifest_digest,
        validate_actor_split,
    )

    try:
        materialized = tuple(records)
    except TypeError as error:
        raise ValueError("validated actor split records must be a sequence") from error
    if not isinstance(assignment, Mapping):
        raise ValueError("validated actor split assignment must be a mapping")
    supplied = dict(assignment)
    validate_actor_split(materialized, supplied)
    expected = build_actor_split(materialized, seed_digest)
    if supplied != expected:
        raise ValueError(
            "validated actor split assignment does not match deterministic split"
        )
    canonical = tuple(
        (actor, expected[actor]) for actor in sorted(expected)
    )
    manifest_sha256 = split_manifest_digest(
        materialized,
        expected,
        seed_digest,
    ).upper()
    return materialized, canonical, manifest_sha256


def mint_validated_split_assignment(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
    seed_digest: str,
) -> ValidatedSplitAssignment:
    materialized, canonical, manifest_sha256 = (
        _validate_split_assignment_components(
            records,
            assignment,
            seed_digest,
        )
    )
    result = object.__new__(ValidatedSplitAssignment)
    for name, value in (
        ("_records", materialized),
        ("_assignment", canonical),
        ("_seed_digest", seed_digest),
        ("_manifest_sha256", manifest_sha256),
    ):
        object.__setattr__(result, name, value)
    return result


def _verify_validated_split_assignment(
    split_assignment: Any,
) -> tuple[dict[str, str], str, str]:
    if type(split_assignment) is not ValidatedSplitAssignment:
        raise ValueError(
            "partition evidence requires a validated actor split assignment"
        )
    materialized, canonical, manifest_sha256 = (
        _validate_split_assignment_components(
            split_assignment._records,
            dict(split_assignment._assignment),
            split_assignment._seed_digest,
        )
    )
    if (
        materialized != split_assignment._records
        or canonical != split_assignment._assignment
        or manifest_sha256 != split_assignment._manifest_sha256
    ):
        raise ValueError("validated actor split assignment commitment changed")
    return dict(canonical), split_assignment._seed_digest, manifest_sha256


@dataclass(frozen=True, init=False)
class PartitionEvidence:
    _payload: dict[str, Any]
    _row_ids: tuple[str, ...]
    _actor_ids: tuple[str, ...]
    _labels: np.ndarray
    _split_assignment: ValidatedSplitAssignment
    _configuration: dict[str, Any]
    _environment_lock: dict[str, Any]
    _feature_schema: dict[str, Any]
    _split_schema: dict[str, Any]
    _features: np.ndarray | None
    _sentences: np.ndarray | None
    _probabilities: dict[str, np.ndarray] | None
    _model_identity: dict[str, Any]

    def __init__(self, *_: Any, **__: Any) -> None:
        raise TypeError("partition evidence is minted after validation")

    def to_payload(self) -> dict[str, Any]:
        return copy.deepcopy(self._payload)


class _BoundPayload(Mapping[str, Any]):
    __slots__ = ("_payload", "_partition_evidence")

    def __init__(self, *_: Any, **__: Any) -> None:
        raise TypeError("bound evidence payloads are minted by evaluation functions")

    def __getitem__(self, key: str) -> Any:
        return self._payload[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._payload)

    def __len__(self) -> int:
        return len(self._payload)

    def to_payload(self) -> dict[str, Any]:
        return copy.deepcopy(self._payload)


class CalibrationEvidence(_BoundPayload):
    pass


class EvaluationEvidence(_BoundPayload):
    pass


class BootstrapEvidence(_BoundPayload):
    pass


class DecisionEvidence(_BoundPayload):
    pass


def _mint_bound_payload(
    evidence_type: type[_BoundPayload],
    payload: dict[str, Any],
    partition_evidence: PartitionEvidence,
) -> _BoundPayload:
    sealed = copy.deepcopy(payload)
    sealed["self_sha256"] = canonical_payload_sha256(sealed)
    result = object.__new__(evidence_type)
    object.__setattr__(result, "_payload", sealed)
    object.__setattr__(result, "_partition_evidence", partition_evidence)
    return result


def mint_partition_evidence(
    *,
    partition_role: str,
    row_ids: Sequence[str],
    actor_ids: Sequence[str],
    labels: np.ndarray,
    split_assignment: ValidatedSplitAssignment,
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
    features: np.ndarray | None,
    sentences: np.ndarray | None,
    probabilities: Mapping[str, np.ndarray] | None,
    model_identity: Mapping[str, Any],
) -> PartitionEvidence:
    role = validate_partition_role(
        partition_role,
        (
            "training_discovery",
            "calibration",
            "balanced_diagnostic",
            "final_lockbox",
        ),
    )
    validated_config = validate_config(copy.deepcopy(dict(configuration)))
    validated_environment = validate_environment_lock(
        copy.deepcopy(dict(environment_lock))
    )
    validated_feature = validate_feature_schema(
        copy.deepcopy(dict(feature_schema))
    )
    validated_split = validate_split_schema(copy.deepcopy(dict(split_schema)))
    if (
        not isinstance(model_identity, Mapping)
        or dict(model_identity) != frozen_model_identity(
            model_identity.get("acoustic", {})
            .get("classifier", {})
            .get("random_state")
        )
    ):
        raise ValueError("model identity does not match frozen model contract")
    model_identity_dict = copy.deepcopy(dict(model_identity))
    seed = model_identity_dict["acoustic"]["classifier"]["random_state"]

    try:
        rows = tuple(row_ids)
        actors = tuple(actor_ids)
    except TypeError as error:
        raise ValueError("row and actor IDs must be sequences") from error
    if (
        not rows
        or len(rows) != len(set(rows))
        or any(
            type(row) is not str or not row or row.strip() != row
            for row in rows
        )
    ):
        raise ValueError("case-order row IDs must be unique non-empty strings")
    if len(actors) != len(rows):
        raise ValueError("actor IDs do not match case-order rows")
    validated_labels, validated_actors = validate_labels_and_actors(
        labels,
        actors,
        expected_rows=len(rows),
    )
    assignment, split_seed_digest, split_manifest_sha = (
        _verify_validated_split_assignment(split_assignment)
    )
    if (
        any(actor not in assignment for actor in validated_actors)
        or any(assignment[actor] != role for actor in validated_actors)
    ):
        raise ValueError(
            "actor assignment membership does not match declared partition"
        )

    probability_arrays: dict[str, np.ndarray] | None = None
    feature_copy: np.ndarray | None = None
    sentence_copy: np.ndarray | None = None
    if role == "training_discovery":
        if probabilities is not None or features is None or sentences is None:
            raise ValueError(
                "training_discovery evidence requires features/sentences only"
            )
        validated_features, validated_sentences, _, _ = validate_fit_inputs(
            features,
            sentences,
            validated_labels,
            seed,
            partition_role=role,
            class_order=CLASS_ORDER,
        )
        feature_copy = validated_features.copy()
        sentence_copy = validated_sentences.copy()
        label_input_commitment = _canonical_sha256({
            "labels_sha256": _array_commitment(validated_labels),
            "features_sha256": _array_commitment(validated_features),
            "sentences_sha256": _array_commitment(validated_sentences),
        })
        probability_commitment = _canonical_sha256({
            "status": "not_applicable_before_fit"
        })
    else:
        if features is not None or sentences is not None or probabilities is None:
            raise ValueError(
                "non-training evidence requires probabilities only"
            )
        probability_arrays, probability_rows = validate_probability_inputs(
            probabilities,
            class_order=CLASS_ORDER,
            expected_rows=len(rows),
        )
        if probability_rows != len(rows):
            raise ValueError("probability rows do not match case-order rows")
        probability_arrays = {
            key: probability_arrays[key].copy() for key in MODEL_KEYS
        }
        label_input_commitment = _canonical_sha256({
            "labels_sha256": _array_commitment(validated_labels),
        })
        probability_commitment = _canonical_sha256({
            key: _array_commitment(probability_arrays[key])
            for key in MODEL_KEYS
        })

    configuration_sha = _canonical_sha256(validated_config)
    environment_sha = _canonical_sha256(validated_environment)
    feature_sha = _canonical_sha256(validated_feature)
    split_schema_sha = _canonical_sha256(validated_split)
    if split_seed_digest != configuration_sha.lower():
        raise ValueError(
            "validated actor split seed does not match configuration commitment"
        )
    assignment_sha = _canonical_sha256([
        [actor, assignment[actor]] for actor in sorted(assignment)
    ])
    payload = {
        "schema_id": "emotion-state-phase-b-partition-evidence-v1",
        "partition_role": role,
        "configuration_sha256": configuration_sha,
        "environment_lock_sha256": environment_sha,
        "feature_schema_sha256": feature_sha,
        "split_schema_sha256": split_schema_sha,
        "split_manifest_sha256": split_manifest_sha,
        "assignment_sha256": assignment_sha,
        "row_commitment_sha256": _canonical_sha256(list(rows)),
        "actor_commitment_sha256": _canonical_sha256(list(validated_actors)),
        "label_input_commitment_sha256": label_input_commitment,
        "model_class_commitment_sha256": _canonical_sha256(
            model_identity_dict
        ),
        "probability_commitment_sha256": probability_commitment,
        "case_count": len(rows),
        "unique_actor_count": len(set(validated_actors)),
    }
    payload["self_sha256"] = canonical_payload_sha256(payload)
    validate_provenance_payload(payload, expected_role=role)

    evidence = object.__new__(PartitionEvidence)
    for name, value in (
        ("_payload", payload),
        ("_row_ids", rows),
        ("_actor_ids", validated_actors),
        ("_labels", validated_labels.copy()),
        ("_split_assignment", split_assignment),
        ("_configuration", copy.deepcopy(validated_config)),
        ("_environment_lock", copy.deepcopy(validated_environment)),
        ("_feature_schema", copy.deepcopy(validated_feature)),
        ("_split_schema", copy.deepcopy(validated_split)),
        ("_features", feature_copy),
        ("_sentences", sentence_copy),
        ("_probabilities", probability_arrays),
        ("_model_identity", model_identity_dict),
    ):
        object.__setattr__(evidence, name, value)
    return evidence


def _verify_partition_evidence(
    evidence: Any,
    *,
    expected_role: str,
    labels: np.ndarray,
    actor_ids: Sequence[str] | None = None,
    features: np.ndarray | None = None,
    sentences: np.ndarray | None = None,
    probabilities: Mapping[str, np.ndarray] | None = None,
    expected_seed: int | None = None,
) -> PartitionEvidence:
    if type(evidence) is not PartitionEvidence:
        raise ValueError("partition-sensitive input requires bound evidence")
    validate_provenance_payload(
        evidence._payload,
        expected_role=expected_role,
    )
    actors = evidence._actor_ids if actor_ids is None else tuple(actor_ids)
    reminted = mint_partition_evidence(
        partition_role=expected_role,
        row_ids=evidence._row_ids,
        actor_ids=actors,
        labels=labels,
        split_assignment=evidence._split_assignment,
        configuration=evidence._configuration,
        environment_lock=evidence._environment_lock,
        feature_schema=evidence._feature_schema,
        split_schema=evidence._split_schema,
        features=features,
        sentences=sentences,
        probabilities=probabilities,
        model_identity=evidence._model_identity,
    )
    if reminted._payload != evidence._payload:
        if (
            reminted._payload["probability_commitment_sha256"]
            != evidence._payload["probability_commitment_sha256"]
        ):
            raise ValueError("probability commitment does not match exact inputs")
        raise ValueError("partition evidence commitment does not match exact inputs")
    if (
        expected_seed is not None
        and evidence._model_identity["acoustic"]["classifier"]["random_state"]
        != expected_seed
    ):
        raise ValueError("model seed does not match evidence model identity")
    return evidence


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
    evidence: PartitionEvidence,
) -> dict[str, object]:
    bound = _verify_partition_evidence(
        evidence,
        expected_role="training_discovery",
        labels=training_labels,
        features=training_features,
        sentences=training_sentences,
        expected_seed=seed,
    )
    features, sentences, labels, validated_seed = validate_fit_inputs(
        training_features,
        training_sentences,
        training_labels,
        seed,
        partition_role=bound._payload["partition_role"],
        class_order=CLASS_ORDER,
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
    evidence: PartitionEvidence,
) -> CalibrationEvidence:
    bound = _verify_partition_evidence(
        evidence,
        expected_role="calibration",
        labels=evidence._labels if type(evidence) is PartitionEvidence else None,
        probabilities=probabilities,
    )
    if tuple(targets) != COVERAGE_TARGETS:
        raise ValueError("calibration targets must be exactly 1.0, 0.8, 0.6")
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=CLASS_ORDER,
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
        "provenance": bound.to_payload(),
    }
    result_evidence = _mint_bound_payload(
        CalibrationEvidence,
        result,
        bound,
    )
    validate_calibration_result(result_evidence.to_payload())
    return result_evidence


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
    thresholds: CalibrationEvidence,
    *,
    evidence: PartitionEvidence,
) -> EvaluationEvidence:
    if type(thresholds) is not CalibrationEvidence:
        raise ValueError("thresholds require bound calibration evidence")
    validate_calibration_result(thresholds.to_payload())
    if type(evidence) is not PartitionEvidence:
        raise ValueError("evaluation requires bound partition evidence")
    role = validate_partition_role(
        evidence._payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    bound = _verify_partition_evidence(
        evidence,
        expected_role=role,
        labels=labels,
        actor_ids=actor_ids,
        probabilities=probabilities,
    )
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=CLASS_ORDER,
    )
    validated_labels, actors = validate_labels_and_actors(
        labels,
        actor_ids,
        expected_rows=row_count,
    )
    validated_thresholds = validate_calibration_result(
        thresholds.to_payload()
    )
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
        "provenance": bound.to_payload(),
    }
    result_evidence = _mint_bound_payload(
        EvaluationEvidence,
        result,
        bound,
    )
    validate_evaluation_result(
        result_evidence.to_payload(),
        expected_role=role,
    )
    return result_evidence


def paired_actor_bootstrap(
    labels: np.ndarray,
    probabilities: Mapping[str, np.ndarray],
    actor_ids: Sequence[str],
    resamples: int,
    seed: int,
    *,
    evidence: PartitionEvidence,
) -> BootstrapEvidence:
    bound = _verify_partition_evidence(
        evidence,
        expected_role="final_lockbox",
        labels=labels,
        actor_ids=actor_ids,
        probabilities=probabilities,
    )
    if type(resamples) is not int or resamples != BOOTSTRAP_RESAMPLES:
        raise ValueError("paired actor bootstrap requires exactly 2,000 resamples")
    configuration_sha256 = bound._payload["configuration_sha256"]
    if (
        type(seed) is not int
        or seed != int(configuration_sha256[:16], 16)
    ):
        raise ValueError(
            "bootstrap seed must derive from the configuration SHA-256"
        )
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=CLASS_ORDER,
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
        "provenance": bound.to_payload(),
    }
    result_evidence = _mint_bound_payload(
        BootstrapEvidence,
        result,
        bound,
    )
    validate_bootstrap_result(result_evidence.to_payload())
    return result_evidence


def build_decision_evidence(
    evaluation: EvaluationEvidence,
    bootstrap: BootstrapEvidence,
    *,
    evidence: PartitionEvidence,
    sentence_driven_apparent_lift: bool,
    eligible_slice_reversal: bool,
    eligible_slice_instability: bool,
    confidence_abstention_improves: bool,
) -> DecisionEvidence:
    if (
        type(evaluation) is not EvaluationEvidence
        or type(bootstrap) is not BootstrapEvidence
        or type(evidence) is not PartitionEvidence
    ):
        raise ValueError("decision construction requires bound evidence objects")
    _verify_partition_evidence(
        evidence,
        expected_role="final_lockbox",
        labels=evidence._labels,
        actor_ids=evidence._actor_ids,
        probabilities=evidence._probabilities,
    )
    validated_evaluation = validate_evaluation_result(
        evaluation.to_payload(),
        expected_role="final_lockbox",
    )
    validated_bootstrap = validate_bootstrap_result(bootstrap.to_payload())
    if (
        evaluation._partition_evidence is not evidence
        or bootstrap._partition_evidence is not evidence
        or validated_evaluation["provenance"] != evidence._payload
        or validated_bootstrap["provenance"] != evidence._payload
        or validated_evaluation["provenance"]
        != validated_bootstrap["provenance"]
    ):
        raise ValueError(
            "evaluation/bootstrap provenance commitments do not match"
        )
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
        "provenance": evidence.to_payload(),
    }
    all_valid = {
        "material_valid": True,
        "environment_valid": True,
        "split_valid": True,
        "leakage_free": True,
        "deterministic": True,
        "lockbox_valid": True,
    }
    result_evidence = _mint_bound_payload(
        DecisionEvidence,
        result,
        evidence,
    )
    validate_decision_inputs(result_evidence.to_payload(), all_valid)
    return result_evidence


def decide_experiment(
    metrics: DecisionEvidence,
    validity: Mapping[str, bool],
) -> str:
    if type(metrics) is not DecisionEvidence:
        raise ValueError(
            "decide_experiment requires bound decision evidence"
        )
    if (
        type(metrics._partition_evidence) is not PartitionEvidence
        or metrics["provenance"] != metrics._partition_evidence._payload
    ):
        raise ValueError("bound decision evidence provenance does not match")
    validated_metrics, validated_validity = validate_decision_inputs(
        metrics.to_payload(),
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
