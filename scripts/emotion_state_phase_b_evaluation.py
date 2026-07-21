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
from typing import TYPE_CHECKING, Any

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
    validate_phase_b_partition_authority_cache,
    validate_phase_b_split_manifest,
    validate_partition_role,
    validate_probability_inputs,
    validate_probability_evidence_payload,
    validate_provenance_payload,
    validate_split_schema,
    canonical_payload_sha256,
)

if TYPE_CHECKING:
    from scripts.emotion_state_phase_b_public_pipeline import (
        SourceByteIdentity,
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


def _parse_crema_clip_identity(clip_stem: Any) -> tuple[str, str]:
    if type(clip_stem) is not str:
        raise ValueError("invalid CREMA-D clip identity")
    match = CLIP_PATTERN.fullmatch(clip_stem)
    if match is None:
        raise ValueError("invalid CREMA-D clip identity")
    return match.group("actor"), match.group("sentence")


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


def _rows_bytes(
    source_bytes: bytes,
    required: tuple[str, ...],
    source_name: str,
) -> tuple[list[dict[str, str]], str]:
    if type(source_bytes) is not bytes:
        raise TypeError(f"{source_name} bytes must be bytes")
    try:
        with io.TextIOWrapper(
            io.BytesIO(source_bytes),
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or tuple(reader.fieldnames) != required:
                raise ValueError(f"unexpected CSV schema: {source_name}")
            rows: list[dict[str, str]] = []
            for row in reader:
                if (
                    tuple(row) != required
                    or any(not isinstance(row[key], str) for key in required)
                ):
                    raise ValueError(f"unexpected CSV row: {source_name}")
                rows.append({key: row[key].strip() for key in required})
    except csv.Error as error:
        raise ValueError(f"malformed CSV row: {source_name}") from error
    return rows, hashlib.sha256(source_bytes).hexdigest().upper()


def _rows(path: Path, required: tuple[str, ...]) -> tuple[list[dict[str, str]], str]:
    source = Path(path)
    return _rows_bytes(source.read_bytes(), required, source.name)


def _winners(distribution: Counter[str]) -> tuple[str, ...]:
    maximum = max(distribution.values(), default=0)
    return tuple(sorted(
        label for label, count in distribution.items()
        if count == maximum and maximum > 0
    ))


def _entropy(distribution: Counter[str]) -> float | None:
    cells = tuple(sorted(distribution.items(), key=lambda cell: cell[0]))
    total = sum(count for _label, count in cells)
    if total == 0:
        return None
    return _canonical_vote_metrics(cells)[1]


def _canonical_vote_metrics(
    vote_distribution: Sequence[tuple[str, int]],
) -> tuple[float, float]:
    cells = tuple(sorted(vote_distribution, key=lambda cell: cell[0]))
    total = sum(count for _label, count in cells)
    agreement = max(count for _label, count in cells) / total
    entropy_terms = (
        (count / total) * math.log2(count / total)
        for _label, count in cells
        if count
    )
    entropy = -sum(entropy_terms)
    agreement = 0.0 if agreement == 0.0 else float(agreement)
    entropy = 0.0 if entropy == 0.0 else float(entropy)
    return agreement, entropy


def load_crema_reference_labels(
    finished_path: Path,
    summary_path: Path,
    included_clip_stems: Collection[str],
) -> tuple[tuple[CremaLabelRecord, ...], dict[str, Any]]:
    return load_crema_reference_labels_bytes(
        Path(finished_path).read_bytes(),
        Path(summary_path).read_bytes(),
        included_clip_stems,
    )


def load_crema_reference_labels_bytes(
    finished_responses_bytes: bytes,
    summary_table_bytes: bytes,
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
    finished_rows, finished_responses_sha256 = _rows_bytes(
        finished_responses_bytes,
        finished_header,
        "finishedResponses.csv",
    )
    raw_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in finished_rows:
        if row[RAW_MODALITY_FIELD] != RAW_AUDIO_MODALITY:
            continue
        if row[RAW_LABEL_FIELD] not in LABELS:
            raise ValueError("invalid raw audio-perception label")
        raw_groups[row[RAW_JOIN_FIELD]][row[RAW_LABEL_FIELD]] += 1

    summary_rows, summary_table_sha256 = _rows_bytes(
        summary_table_bytes,
        summary_header,
        "summaryTable.csv",
    )
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
        try:
            actor_id, sentence_id = _parse_crema_clip_identity(stem)
        except ValueError as error:
            raise ValueError("invalid included CREMA-D clip stem") from error
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
        vote_agreement, vote_entropy = _canonical_vote_metrics(
            tuple(distribution.items())
        )
        records.append(CremaLabelRecord(
            clip_stem=stem,
            actor_id=actor_id,
            sentence_id=sentence_id,
            label=label,
            abstention_reason=reason,
            vote_distribution=tuple(sorted(distribution.items())),
            vote_agreement=vote_agreement,
            vote_entropy=vote_entropy,
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


class _ImmutableArtifact(Mapping[str, Any]):
    __slots__ = ("__canonical_bytes", "__mint_digest", "__links")

    def __init__(self, *_: Any, **__: Any) -> None:
        raise TypeError("bound evidence artifacts are minted after validation")

    def __setattr__(self, _name: str, _value: Any) -> None:
        raise AttributeError("bound evidence artifacts are immutable")

    def _fresh_payload(self) -> dict[str, Any]:
        canonical = object.__getattribute__(
            self,
            "_ImmutableArtifact__canonical_bytes",
        )
        return json.loads(canonical.decode("ascii"))

    def __getitem__(self, key: str) -> Any:
        return self._fresh_payload()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._fresh_payload())

    def __len__(self) -> int:
        return len(self._fresh_payload())

    @property
    def mint_sha256(self) -> str:
        return object.__getattribute__(
            self,
            "_ImmutableArtifact__mint_digest",
        )

    def to_payload(self) -> dict[str, Any]:
        return self._fresh_payload()


def _sealed_payload(payload: Mapping[str, Any]) -> tuple[bytes, str]:
    sealed = copy.deepcopy(dict(payload))
    sealed["self_sha256"] = canonical_payload_sha256(sealed)
    canonical = json.dumps(
        sealed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return canonical, hashlib.sha256(canonical).hexdigest().upper()


def _mint_artifact(
    artifact_type: type[_ImmutableArtifact],
    payload: Mapping[str, Any],
    *links: Any,
) -> _ImmutableArtifact:
    canonical, mint_digest = _sealed_payload(payload)
    result = object.__new__(artifact_type)
    object.__setattr__(
        result,
        "_ImmutableArtifact__canonical_bytes",
        canonical,
    )
    object.__setattr__(
        result,
        "_ImmutableArtifact__mint_digest",
        mint_digest,
    )
    object.__setattr__(
        result,
        "_ImmutableArtifact__links",
        tuple(links),
    )
    return result


def _artifact_links(artifact: _ImmutableArtifact) -> tuple[Any, ...]:
    return object.__getattribute__(
        artifact,
        "_ImmutableArtifact__links",
    )


def _verify_artifact_mint(
    artifact: Any,
    expected_type: type[_ImmutableArtifact],
) -> dict[str, Any]:
    if type(artifact) is not expected_type:
        raise TypeError(
            f"{expected_type.__name__} is required; arbitrary mappings reject"
        )
    canonical = object.__getattribute__(
        artifact,
        "_ImmutableArtifact__canonical_bytes",
    )
    mint_digest = object.__getattribute__(
        artifact,
        "_ImmutableArtifact__mint_digest",
    )
    if hashlib.sha256(canonical).hexdigest().upper() != mint_digest:
        raise ValueError("bound evidence mint digest does not match canonical bytes")
    payload = json.loads(canonical.decode("ascii"))
    expected_canonical, expected_mint = _sealed_payload(payload)
    if expected_canonical != canonical or expected_mint != mint_digest:
        raise ValueError("bound evidence canonical bytes changed after mint")
    validate_payload_self_hash(payload, expected_type.__name__)
    return payload


@dataclass(frozen=True, slots=True)
class _ValidatedSplitState:
    records: tuple[CremaLabelRecord, ...]
    acoustic_bindings: tuple[tuple[str, str, int], ...]
    assignment: tuple[tuple[str, str], ...]
    seed_digest: str
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class _ValidatedPartitionAuthorityState:
    records: tuple[CremaLabelRecord, ...]
    acoustic_bindings: tuple[tuple[str, str, int], ...]
    role: str
    seed_digest: str
    manifest_sha256: str
    assignment_sha256: str


@dataclass(frozen=True, slots=True)
class _VerifiedPartitionAuthoritySnapshot:
    records: tuple[CremaLabelRecord, ...]
    acoustic_bindings: tuple[tuple[str, str, int], ...]
    role: str
    seed_digest: str
    manifest_sha256: str
    assignment_sha256: str


@dataclass(frozen=True)
class _PartitionState:
    rows: tuple[str, ...]
    actors: tuple[str, ...]
    labels: tuple[str, ...]
    sentences: tuple[str, ...]
    features: np.ndarray
    split_assignment: "ValidatedSplitAssignment | ValidatedPartitionAuthority"
    configuration: dict[str, Any]
    environment_lock: dict[str, Any]
    feature_schema: dict[str, Any]
    split_schema: dict[str, Any]
    model_identity: dict[str, Any]


@dataclass(frozen=True)
class _FittedModelState:
    models: tuple[tuple[str, object], ...]
    model_state_sha256: str
    training_evidence: "PartitionEvidence"


@dataclass(frozen=True)
class _ProbabilityState:
    arrays: tuple[tuple[str, np.ndarray], ...]
    fitted_models: "FittedModelEvidence"
    partition_evidence: "PartitionEvidence"


class ValidatedSplitAssignment(_ImmutableArtifact):
    __slots__ = ()


class ValidatedPartitionAuthority(_ImmutableArtifact):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class ValidatedPartitionRecord:
    label_record: CremaLabelRecord
    audio_sha256: str
    audio_size_bytes: int


class PartitionEvidence(_ImmutableArtifact):
    __slots__ = ()


class FittedModelEvidence(_ImmutableArtifact):
    __slots__ = ()


class ProbabilityEvidence(_ImmutableArtifact):
    __slots__ = ()


class CalibrationEvidence(_ImmutableArtifact):
    __slots__ = ()


class EvaluationEvidence(_ImmutableArtifact):
    __slots__ = ()


class BootstrapEvidence(_ImmutableArtifact):
    __slots__ = ()


class SliceAnalysisEvidence(_ImmutableArtifact):
    __slots__ = ()


class DecisionEvidence(_ImmutableArtifact):
    __slots__ = ()


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
        supplied_records = tuple(records)
    except TypeError as error:
        raise ValueError("validated actor split records must be a sequence") from error
    materialized = tuple(
        _canonical_partition_authority_record(record)
        for record in supplied_records
    )
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


_NONFINAL_PARTITION_ROLES = (
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
)
_PARTITION_ACTOR_COUNTS = {
    "training_discovery": 35,
    "calibration": 13,
    "balanced_diagnostic": 13,
    "final_lockbox": 30,
}


def _require_private_sha256(
    value: Any,
    *,
    uppercase: bool,
    name: str,
) -> str:
    pattern = r"[0-9A-F]{64}" if uppercase else r"[0-9a-f]{64}"
    if type(value) is not str or re.fullmatch(pattern, value) is None:
        raise ValueError(f"{name} private state is invalid")
    return value


def _validate_split_private_state_shape(
    state: _ValidatedSplitState,
) -> None:
    if type(state.records) is not tuple:
        raise ValueError("validated actor split records state must be an exact tuple")
    if type(state.acoustic_bindings) is not tuple:
        raise ValueError(
            "validated actor split acoustic state must be an exact tuple"
        )
    if (
        type(state.assignment) is not tuple
        or any(
            type(cell) is not tuple
            or len(cell) != 2
            or type(cell[0]) is not str
            or type(cell[1]) is not str
            or cell[1] not in (*_NONFINAL_PARTITION_ROLES, "final_lockbox")
            for cell in state.assignment
        )
    ):
        raise ValueError(
            "validated actor split assignment state must use exact tuples"
        )
    _require_private_sha256(
        state.seed_digest,
        uppercase=False,
        name="validated actor split seed",
    )
    _require_private_sha256(
        state.manifest_sha256,
        uppercase=True,
        name="validated actor split manifest",
    )


def _validate_partition_private_state_shape(
    state: _ValidatedPartitionAuthorityState,
) -> None:
    if type(state.records) is not tuple:
        raise ValueError(
            "validated partition authority records state must be an exact tuple"
        )
    if type(state.acoustic_bindings) is not tuple:
        raise ValueError(
            "validated partition authority acoustic state must be an exact tuple"
        )
    validate_partition_role(state.role, _NONFINAL_PARTITION_ROLES)
    _require_private_sha256(
        state.seed_digest,
        uppercase=False,
        name="validated partition authority seed",
    )
    _require_private_sha256(
        state.manifest_sha256,
        uppercase=True,
        name="validated partition authority manifest",
    )
    _require_private_sha256(
        state.assignment_sha256,
        uppercase=True,
        name="validated partition authority assignment",
    )


def _canonical_partition_authority_record(
    record: Any,
) -> CremaLabelRecord:
    if type(record) is not CremaLabelRecord:
        raise ValueError(
            "partition authority records must be exact eligible CREMA records"
        )
    try:
        clip_actor_id, clip_sentence_id = _parse_crema_clip_identity(
            record.clip_stem
        )
    except ValueError as error:
        raise ValueError("partition authority clip identity is invalid") from error
    if (
        clip_actor_id != record.actor_id
        or clip_sentence_id != record.sentence_id
    ):
        raise ValueError(
            "partition authority clip identity does not match record identity"
        )
    if (
        type(record.actor_id) is not str
        or re.fullmatch(r"\d{4}", record.actor_id) is None
        or type(record.sentence_id) is not str
        or re.fullmatch(r"[A-Z0-9]{3}", record.sentence_id) is None
        or type(record.label) is not str
        or record.label not in LABELS
        or record.abstention_reason is not None
    ):
        raise ValueError(
            "partition authority records must be eligible CREMA records"
        )
    distribution = record.vote_distribution
    if (
        type(distribution) is not tuple
        or not distribution
        or any(
            type(cell) is not tuple
            or len(cell) != 2
            or type(cell[0]) is not str
            or cell[0] not in LABELS
            or type(cell[1]) is not int
            or cell[1] <= 0
            for cell in distribution
        )
        or tuple(sorted(distribution)) != distribution
        or len({cell[0] for cell in distribution}) != len(distribution)
    ):
        raise ValueError("partition authority vote distribution is invalid")
    counts = Counter(dict(distribution))
    if _winners(counts) != (record.label,):
        raise ValueError(
            "partition authority label does not match the unique vote winner"
        )
    expected_agreement, expected_entropy = _canonical_vote_metrics(
        distribution
    )
    if (
        type(record.vote_agreement) is not float
        or not math.isfinite(record.vote_agreement)
    ):
        raise ValueError("partition authority vote agreement is invalid")
    vote_agreement = (
        0.0 if record.vote_agreement == 0.0
        else float(record.vote_agreement)
    )
    if vote_agreement.hex() != expected_agreement.hex():
        raise ValueError("partition authority vote agreement is invalid")
    if (
        type(record.vote_entropy) is not float
        or not math.isfinite(record.vote_entropy)
    ):
        raise ValueError("partition authority vote entropy is invalid")
    vote_entropy = (
        0.0 if record.vote_entropy == 0.0
        else float(record.vote_entropy)
    )
    if vote_entropy.hex() != expected_entropy.hex():
        raise ValueError("partition authority vote entropy is invalid")
    return CremaLabelRecord(
        clip_stem=record.clip_stem,
        actor_id=record.actor_id,
        sentence_id=record.sentence_id,
        label=record.label,
        abstention_reason=None,
        vote_distribution=tuple(distribution),
        vote_agreement=vote_agreement,
        vote_entropy=vote_entropy,
    )


def _validate_partition_authority_record(record: Any) -> None:
    _canonical_partition_authority_record(record)


_CREMA_LABEL_RECORD_FIELDS = (
    "clip_stem",
    "actor_id",
    "sentence_id",
    "label",
    "abstention_reason",
    "vote_distribution",
    "vote_agreement",
    "vote_entropy",
)


def _private_record_matches_canonical(
    record: Any,
    canonical: CremaLabelRecord,
) -> bool:
    if (
        type(record) is not CremaLabelRecord
        or set(vars(record)) != set(_CREMA_LABEL_RECORD_FIELDS)
    ):
        return False
    for field in _CREMA_LABEL_RECORD_FIELDS:
        supplied = getattr(record, field)
        expected = getattr(canonical, field)
        if field in ("vote_agreement", "vote_entropy"):
            if (
                type(supplied) is not float
                or type(expected) is not float
                or supplied.hex() != expected.hex()
            ):
                return False
        elif supplied != expected:
            return False
    return True


def _validated_internal_acoustic_bindings(
    records: Sequence[CremaLabelRecord],
    bindings: Any,
) -> tuple[tuple[str, str, int], ...]:
    if type(bindings) is not tuple:
        raise ValueError("acoustic bindings private state must be an exact tuple")
    expected_stems = {record.clip_stem for record in records}
    result: list[tuple[str, str, int]] = []
    previous: str | None = None
    for binding in bindings:
        if (
            type(binding) is not tuple
            or len(binding) != 3
            or type(binding[0]) is not str
            or type(binding[1]) is not str
            or re.fullmatch(r"[0-9A-F]{64}", binding[1]) is None
            or type(binding[2]) is not int
            or binding[2] <= 0
        ):
            raise ValueError("acoustic bindings private state is invalid")
        if previous is not None and binding[0] <= previous:
            raise ValueError(
                "acoustic bindings private state must have ascending unique stems"
            )
        previous = binding[0]
        result.append((binding[0], binding[1], binding[2]))
    if {binding[0] for binding in result} != expected_stems:
        raise ValueError("acoustic bindings do not match eligible record stems")
    return tuple(result)


def _validate_acoustic_sources(
    records: Sequence[CremaLabelRecord],
    acoustic_sources: Mapping[str, "SourceByteIdentity"],
) -> tuple[tuple[str, str, int], ...]:
    from scripts.emotion_state_phase_b_public_pipeline import (
        SourceByteIdentity,
    )

    if not isinstance(acoustic_sources, Mapping):
        raise ValueError("acoustic sources must be a mapping")
    supplied_keys = tuple(acoustic_sources)
    if any(type(key) is not str for key in supplied_keys):
        raise ValueError("acoustic source keys must be exact strings")
    expected_stems = {record.clip_stem for record in records}
    if (
        len(supplied_keys) != len(set(supplied_keys))
        or set(supplied_keys) != expected_stems
    ):
        raise ValueError("acoustic source keys must exactly match eligible stems")
    result: list[tuple[str, str, int]] = []
    prefix = (
        "data/public/emotion-state/crema-d-v1.0/repository/AudioWAV/"
    )
    for stem in sorted(expected_stems):
        source = acoustic_sources[stem]
        if type(source) is not SourceByteIdentity:
            raise ValueError("acoustic source identity must have exact type")
        if (
            type(source.project_relative_path) is not str
            or source.project_relative_path != f"{prefix}{stem}.wav"
        ):
            raise ValueError("acoustic source path is not canonical")
        if (
            type(source.sha256) is not str
            or re.fullmatch(r"[0-9A-F]{64}", source.sha256) is None
        ):
            raise ValueError("acoustic source SHA-256 is invalid")
        if type(source.size_bytes) is not int or source.size_bytes <= 0:
            raise ValueError("acoustic source size is invalid")
        result.append((stem, source.sha256, source.size_bytes))
    return tuple(result)


def _canonical_cache_record(
    record: CremaLabelRecord,
    binding: tuple[str, str, int],
) -> dict[str, Any]:
    canonical = _canonical_partition_authority_record(record)
    if binding[0] != canonical.clip_stem:
        raise ValueError("acoustic binding does not match record identity")
    return {
        "clip_stem": canonical.clip_stem,
        "actor_id": canonical.actor_id,
        "sentence_id": canonical.sentence_id,
        "label": canonical.label,
        "abstention_reason": canonical.abstention_reason,
        "vote_distribution": [
            [label, count] for label, count in canonical.vote_distribution
        ],
        "vote_agreement": (
            0.0 if canonical.vote_agreement == 0.0
            else float(canonical.vote_agreement)
        ),
        "vote_entropy": (
            0.0 if canonical.vote_entropy == 0.0
            else float(canonical.vote_entropy)
        ),
        "audio_sha256": binding[1],
        "audio_size_bytes": binding[2],
    }


def _partition_authority_cache(
    *,
    role: str,
    records: Sequence[CremaLabelRecord],
    acoustic_bindings: tuple[tuple[str, str, int], ...],
    configuration_sha256: str,
    split_manifest_sha256: str,
    assignment_sha256: str,
) -> dict[str, Any]:
    validated_role = validate_partition_role(
        role,
        _NONFINAL_PARTITION_ROLES,
    )
    try:
        supplied = tuple(records)
    except TypeError as error:
        raise ValueError(
            "partition authority records must be a sequence"
        ) from error
    if not supplied:
        raise ValueError("partition authority records must be eligible CREMA records")
    materialized = tuple(sorted(
        (_canonical_partition_authority_record(record) for record in supplied),
        key=lambda record: record.clip_stem,
    ))
    if len({record.clip_stem for record in materialized}) != len(materialized):
        raise ValueError("partition authority clip identities must be unique")
    validated_bindings = _validated_internal_acoustic_bindings(
        materialized,
        acoustic_bindings,
    )
    binding_by_stem = {
        stem: (stem, sha256, size_bytes)
        for stem, sha256, size_bytes in validated_bindings
    }
    if (
        len({record.actor_id for record in materialized})
        != _PARTITION_ACTOR_COUNTS[validated_role]
    ):
        raise ValueError("partition authority actor count does not match")
    if len({record.sentence_id for record in materialized}) != 12:
        raise ValueError("partition authority sentence count does not match")
    if {record.label for record in materialized} != set(LABELS):
        raise ValueError("partition authority label coverage does not match")
    payload = {
        "schema_id": "emotion-state-phase-b-partition-authority-cache-v2",
        "schema_version": 2,
        "partition_role": validated_role,
        "configuration_sha256": configuration_sha256,
        "split_manifest_sha256": split_manifest_sha256,
        "assignment_sha256": assignment_sha256,
        "records": [
            _canonical_cache_record(
                record,
                binding_by_stem[record.clip_stem],
            )
            for record in materialized
        ],
    }
    payload["self_sha256"] = canonical_payload_sha256(payload)
    return payload


def _full_partition_records(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
) -> dict[str, tuple[CremaLabelRecord, ...]]:
    result = {
        role: tuple(sorted(
            (
                record for record in records
                if assignment[record.actor_id] == role
            ),
            key=lambda record: record.clip_stem,
        ))
        for role in (*_NONFINAL_PARTITION_ROLES, "final_lockbox")
    }
    actor_sets = {
        role: {record.actor_id for record in role_records}
        for role, role_records in result.items()
    }
    record_sets = {
        role: {record.clip_stem for record in role_records}
        for role, role_records in result.items()
    }
    for role, expected_count in _PARTITION_ACTOR_COUNTS.items():
        if len(actor_sets[role]) != expected_count:
            raise ValueError("validated split partition actor count does not match")
    roles = (*_NONFINAL_PARTITION_ROLES, "final_lockbox")
    for index, role in enumerate(roles):
        for other_role in roles[index + 1:]:
            if not actor_sets[role].isdisjoint(actor_sets[other_role]):
                raise ValueError("validated split partition actors overlap")
            if not record_sets[role].isdisjoint(record_sets[other_role]):
                raise ValueError("validated split partition records overlap")
    complete_actors = {record.actor_id for record in records}
    complete_records = {record.clip_stem for record in records}
    if (
        len(set().union(*actor_sets.values())) != 91
        or set().union(*actor_sets.values()) != complete_actors
        or sum(len(items) for items in record_sets.values()) != len(records)
        or set().union(*record_sets.values()) != complete_records
        or len(complete_records) != len(records)
    ):
        raise ValueError("validated split partition totals do not match")
    final_count = len(result["final_lockbox"])
    if not 0 < final_count < len(records):
        raise ValueError("validated split final record count is invalid")
    return result


def _build_validated_split_payload(
    *,
    records: tuple[CremaLabelRecord, ...],
    acoustic_bindings: tuple[tuple[str, str, int], ...],
    assignment: tuple[tuple[str, str], ...],
    seed_digest: str,
    manifest_sha256: str,
) -> dict[str, Any]:
    assignment_by_actor = dict(assignment)
    partitions = _full_partition_records(records, assignment_by_actor)
    validated_bindings = _validated_internal_acoustic_bindings(
        records,
        acoustic_bindings,
    )
    binding_by_stem = {
        stem: (stem, sha256, size_bytes)
        for stem, sha256, size_bytes in validated_bindings
    }
    assignment_sha256 = _canonical_sha256([
        [actor, role] for actor, role in assignment
    ])
    caches = {
        role: _partition_authority_cache(
            role=role,
            records=partitions[role],
            acoustic_bindings=tuple(
                binding_by_stem[record.clip_stem]
                for record in partitions[role]
            ),
            configuration_sha256=seed_digest.upper(),
            split_manifest_sha256=manifest_sha256.upper(),
            assignment_sha256=assignment_sha256,
        )
        for role in _NONFINAL_PARTITION_ROLES
    }
    all_record_preimages = [
        _canonical_cache_record(
            record,
            binding_by_stem[record.clip_stem],
        )
        for record in sorted(records, key=lambda item: item.clip_stem)
    ]
    eligible_authority_commitment = _canonical_sha256({
        "schema_id": "emotion-state-phase-b-eligible-authority-commitment-v2",
        "configuration_sha256": seed_digest.upper(),
        "split_manifest_sha256": manifest_sha256.upper(),
        "assignment_sha256": assignment_sha256,
        "records": all_record_preimages,
    })
    final_records = partitions["final_lockbox"]
    final_authority_commitment = _canonical_sha256({
        "schema_id": "emotion-state-phase-b-final-lockbox-sealed-authority-v2",
        "partition_role": "final_lockbox",
        "configuration_sha256": seed_digest.upper(),
        "split_manifest_sha256": manifest_sha256.upper(),
        "assignment_sha256": assignment_sha256,
        "records": [
            _canonical_cache_record(
                record,
                binding_by_stem[record.clip_stem],
            )
            for record in final_records
        ],
    })
    return {
        "schema_id": "emotion-state-phase-b-validated-split-v2",
        "configuration_sha256": seed_digest.upper(),
        "eligible_record_count": len(records),
        "eligible_actor_count": len(assignment),
        "eligible_authority_commitment_sha256": (
            eligible_authority_commitment
        ),
        "assignment_sha256": assignment_sha256,
        "split_manifest_sha256": manifest_sha256.upper(),
        "partition_authority_sha256": {
            role: caches[role]["self_sha256"]
            for role in _NONFINAL_PARTITION_ROLES
        },
        "final_lockbox_commitment": {
            "eligible_record_count": len(final_records),
            "eligible_actor_count": len({
                record.actor_id for record in final_records
            }),
            "sealed_authority_commitment_sha256": (
                final_authority_commitment
            ),
        },
    }


def mint_validated_split_assignment(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
    seed_digest: str,
    *,
    acoustic_sources: Mapping[str, "SourceByteIdentity"],
) -> ValidatedSplitAssignment:
    materialized, canonical, manifest_sha256 = (
        _validate_split_assignment_components(
            records,
            assignment,
            seed_digest,
        )
    )
    acoustic_bindings = _validate_acoustic_sources(
        materialized,
        acoustic_sources,
    )
    payload = _build_validated_split_payload(
        records=materialized,
        acoustic_bindings=acoustic_bindings,
        assignment=canonical,
        seed_digest=seed_digest,
        manifest_sha256=manifest_sha256,
    )
    state = _ValidatedSplitState(
        records=materialized,
        acoustic_bindings=acoustic_bindings,
        assignment=canonical,
        seed_digest=seed_digest,
        manifest_sha256=manifest_sha256,
    )
    return _mint_artifact(
        ValidatedSplitAssignment,
        payload,
        state,
    )


def _verify_validated_split_assignment(
    split_assignment: Any,
) -> tuple[
    dict[str, str],
    str,
    str,
    tuple[CremaLabelRecord, ...],
    tuple[tuple[str, str, int], ...],
]:
    payload = _verify_artifact_mint(
        split_assignment,
        ValidatedSplitAssignment,
    )
    links = _artifact_links(split_assignment)
    if type(links) is not tuple or len(links) != 1:
        raise ValueError("validated actor split private state is invalid")
    state = links[0]
    if type(state) is not _ValidatedSplitState:
        raise ValueError("validated actor split private state is invalid")
    _validate_split_private_state_shape(state)
    materialized, canonical, manifest_sha256 = (
        _validate_split_assignment_components(
            state.records,
            dict(state.assignment),
            state.seed_digest,
        )
    )
    acoustic_bindings = _validated_internal_acoustic_bindings(
        materialized,
        state.acoustic_bindings,
    )
    if (
        len(materialized) != len(state.records)
        or any(
            not _private_record_matches_canonical(record, canonical_record)
            for record, canonical_record in zip(
                state.records,
                materialized,
                strict=True,
            )
        )
        or acoustic_bindings != state.acoustic_bindings
        or canonical != state.assignment
        or manifest_sha256 != state.manifest_sha256
    ):
        raise ValueError("validated actor split assignment commitment changed")
    expected_payload = _build_validated_split_payload(
        records=materialized,
        acoustic_bindings=acoustic_bindings,
        assignment=canonical,
        seed_digest=state.seed_digest,
        manifest_sha256=manifest_sha256,
    )
    reminted = _mint_artifact(
        ValidatedSplitAssignment,
        expected_payload,
        state,
    )
    if (
        reminted.to_payload() != payload
        or reminted.mint_sha256 != split_assignment.mint_sha256
    ):
        raise ValueError("validated actor split assignment commitment changed")
    validate_phase_b_split_manifest(payload)
    return (
        dict(canonical),
        state.seed_digest,
        manifest_sha256,
        materialized,
        acoustic_bindings,
    )


def serialize_partition_authority_caches(
    split_assignment: ValidatedSplitAssignment,
) -> dict[str, dict[str, Any]]:
    assignment, seed_digest, manifest_sha256, records, acoustic_bindings = (
        _verify_validated_split_assignment(split_assignment)
    )
    binding_by_stem = {
        stem: (stem, sha256, size_bytes)
        for stem, sha256, size_bytes in acoustic_bindings
    }
    split_payload = split_assignment.to_payload()
    result = {
        role: _partition_authority_cache(
            role=role,
            records=tuple(
                record
                for record in records
                if assignment[record.actor_id] == role
            ),
            acoustic_bindings=tuple(
                binding_by_stem[record.clip_stem]
                for record in sorted(
                    (
                        record for record in records
                        if assignment[record.actor_id] == role
                    ),
                    key=lambda record: record.clip_stem,
                )
            ),
            configuration_sha256=seed_digest.upper(),
            split_manifest_sha256=manifest_sha256.upper(),
            assignment_sha256=split_payload["assignment_sha256"],
        )
        for role in _NONFINAL_PARTITION_ROLES
    }
    if {
        role: payload["self_sha256"] for role, payload in result.items()
    } != split_payload["partition_authority_sha256"]:
        raise ValueError("partition authority cache commitments changed")
    return copy.deepcopy(result)


def derive_validated_partition_authority(
    split_assignment: ValidatedSplitAssignment,
    *,
    role: str,
) -> ValidatedPartitionAuthority:
    validated_role = validate_partition_role(
        role,
        _NONFINAL_PARTITION_ROLES,
    )
    caches = serialize_partition_authority_caches(split_assignment)
    return restore_validated_partition_authority_cache(
        caches[validated_role],
        split_assignment.to_payload(),
        role=validated_role,
    )


def _rehydrate_cache_record(item: Mapping[str, Any]) -> CremaLabelRecord:
    distribution = tuple(
        (cell[0], cell[1]) for cell in item["vote_distribution"]
    )
    vote_agreement = (
        0.0 if item["vote_agreement"] == 0.0
        else float(item["vote_agreement"])
    )
    vote_entropy = (
        0.0 if item["vote_entropy"] == 0.0
        else float(item["vote_entropy"])
    )
    return _canonical_partition_authority_record(CremaLabelRecord(
        clip_stem=item["clip_stem"],
        actor_id=item["actor_id"],
        sentence_id=item["sentence_id"],
        label=item["label"],
        abstention_reason=item["abstention_reason"],
        vote_distribution=distribution,
        vote_agreement=vote_agreement,
        vote_entropy=vote_entropy,
    ))


def restore_validated_partition_authority_cache(
    cache: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    *,
    role: str,
) -> ValidatedPartitionAuthority:
    validated_role = validate_partition_role(
        role,
        _NONFINAL_PARTITION_ROLES,
    )
    validated_cache = validate_phase_b_partition_authority_cache(
        cache,
        split_manifest,
        expected_role=validated_role,
    )
    records = tuple(
        _rehydrate_cache_record(item)
        for item in validated_cache["records"]
    )
    bindings = tuple(
        (
            item["clip_stem"],
            item["audio_sha256"],
            item["audio_size_bytes"],
        )
        for item in validated_cache["records"]
    )
    bindings = _validated_internal_acoustic_bindings(records, bindings)
    rebuilt = _partition_authority_cache(
        role=validated_role,
        records=records,
        acoustic_bindings=bindings,
        configuration_sha256=validated_cache["configuration_sha256"],
        split_manifest_sha256=validated_cache["split_manifest_sha256"],
        assignment_sha256=validated_cache["assignment_sha256"],
    )
    if rebuilt != validated_cache:
        raise ValueError(
            "partition authority cache changed during exact rehydration"
        )
    state = _ValidatedPartitionAuthorityState(
        records=records,
        acoustic_bindings=bindings,
        role=validated_role,
        seed_digest=validated_cache["configuration_sha256"].lower(),
        manifest_sha256=validated_cache["split_manifest_sha256"],
        assignment_sha256=validated_cache["assignment_sha256"],
    )
    authority = _mint_artifact(
        ValidatedPartitionAuthority,
        {
            "schema_id": (
                "emotion-state-phase-b-validated-partition-authority-v2"
            ),
            "partition_role": validated_role,
            "configuration_sha256": validated_cache["configuration_sha256"],
            "split_manifest_sha256": validated_cache[
                "split_manifest_sha256"
            ],
            "assignment_sha256": validated_cache["assignment_sha256"],
            "partition_authority_sha256": validated_cache["self_sha256"],
            "eligible_record_count": len(records),
            "eligible_actor_count": len({
                record.actor_id for record in records
            }),
        },
        state,
    )
    _verify_validated_partition_authority(
        authority,
        expected_role=validated_role,
    )
    return authority


def _verify_validated_partition_authority(
    authority: Any,
    *,
    expected_role: str,
) -> tuple[_VerifiedPartitionAuthoritySnapshot, dict[str, Any]]:
    validate_partition_role(expected_role, _NONFINAL_PARTITION_ROLES)
    payload = _verify_artifact_mint(authority, ValidatedPartitionAuthority)
    links = _artifact_links(authority)
    if type(links) is not tuple or len(links) != 1:
        raise ValueError("validated partition authority private state is invalid")
    state = links[0]
    if type(state) is not _ValidatedPartitionAuthorityState:
        raise ValueError("validated partition authority private state is invalid")
    _validate_partition_private_state_shape(state)
    if state.role != expected_role:
        raise ValueError("validated partition authority role does not match")
    records = tuple(
        _canonical_partition_authority_record(record)
        for record in state.records
    )
    if tuple(record.clip_stem for record in records) != tuple(sorted(
        record.clip_stem for record in records
    )):
        raise ValueError(
            "validated partition authority records state is not canonical"
        )
    bindings = _validated_internal_acoustic_bindings(
        records,
        state.acoustic_bindings,
    )
    if (
        len(records) != len(state.records)
        or any(
            not _private_record_matches_canonical(record, canonical_record)
            for record, canonical_record in zip(
                state.records,
                records,
                strict=True,
            )
        )
        or bindings != state.acoustic_bindings
    ):
        raise ValueError(
            "validated partition authority private state changed"
        )
    snapshot = _VerifiedPartitionAuthoritySnapshot(
        records=records,
        acoustic_bindings=bindings,
        role=state.role,
        seed_digest=state.seed_digest,
        manifest_sha256=state.manifest_sha256,
        assignment_sha256=state.assignment_sha256,
    )
    cache = _partition_authority_cache(
        role=snapshot.role,
        records=snapshot.records,
        acoustic_bindings=snapshot.acoustic_bindings,
        configuration_sha256=snapshot.seed_digest.upper(),
        split_manifest_sha256=snapshot.manifest_sha256,
        assignment_sha256=snapshot.assignment_sha256,
    )
    expected_payload = {
        "schema_id": "emotion-state-phase-b-validated-partition-authority-v2",
        "partition_role": snapshot.role,
        "configuration_sha256": snapshot.seed_digest.upper(),
        "split_manifest_sha256": snapshot.manifest_sha256,
        "assignment_sha256": snapshot.assignment_sha256,
        "partition_authority_sha256": cache["self_sha256"],
        "eligible_record_count": len(snapshot.records),
        "eligible_actor_count": len(
            {record.actor_id for record in snapshot.records}
        ),
    }
    reminted = _mint_artifact(
        ValidatedPartitionAuthority,
        expected_payload,
        snapshot,
    )
    if (
        reminted.to_payload() != payload
        or reminted.mint_sha256 != authority.mint_sha256
    ):
        raise ValueError("validated partition authority commitment changed")
    return snapshot, payload


def validated_partition_records(
    authority: ValidatedPartitionAuthority,
    *,
    role: str,
) -> tuple[ValidatedPartitionRecord, ...]:
    validated_role = validate_partition_role(
        role,
        _NONFINAL_PARTITION_ROLES,
    )
    snapshot, _payload = _verify_validated_partition_authority(
        authority,
        expected_role=validated_role,
    )
    bindings = {
        stem: (sha256, size_bytes)
        for stem, sha256, size_bytes in snapshot.acoustic_bindings
    }
    result = []
    for record in snapshot.records:
        fresh_record = _canonical_partition_authority_record(record)
        audio_sha256, audio_size_bytes = bindings[fresh_record.clip_stem]
        result.append(ValidatedPartitionRecord(
            label_record=_canonical_partition_authority_record(fresh_record),
            audio_sha256=audio_sha256,
            audio_size_bytes=audio_size_bytes,
        ))
    return tuple(result)


def mint_partition_evidence(
    *,
    partition_role: str,
    row_ids: Sequence[str],
    actor_ids: Sequence[str],
    labels: np.ndarray,
    sentences: np.ndarray,
    features: np.ndarray,
    upstream_acoustic_source_commitment_sha256: str,
    split_assignment: ValidatedSplitAssignment | ValidatedPartitionAuthority,
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
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

    if isinstance(row_ids, (str, bytes)):
        raise ValueError("row IDs must be a sequence, not bare str/bytes")
    if isinstance(actor_ids, (str, bytes)):
        raise ValueError("actor IDs must be a sequence, not bare str/bytes")
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
    if type(split_assignment) is ValidatedSplitAssignment:
        (
            assignment,
            split_seed_digest,
            split_manifest_sha,
            eligible_records,
            _acoustic_bindings,
        ) = _verify_validated_split_assignment(split_assignment)
        authoritative = tuple(sorted(
            (
                record
                for record in eligible_records
                if assignment[record.actor_id] == role
            ),
            key=lambda record: record.clip_stem,
        ))
        assignment_sha = _canonical_sha256([
            [actor, assignment[actor]] for actor in sorted(assignment)
        ])
    elif type(split_assignment) is ValidatedPartitionAuthority:
        partition_snapshot, _ = _verify_validated_partition_authority(
            split_assignment,
            expected_role=role,
        )
        split_seed_digest = partition_snapshot.seed_digest
        split_manifest_sha = partition_snapshot.manifest_sha256
        authoritative = partition_snapshot.records
        assignment_sha = partition_snapshot.assignment_sha256
    else:
        raise TypeError(
            "ValidatedSplitAssignment or ValidatedPartitionAuthority is required"
        )
    expected_rows = tuple(record.clip_stem for record in authoritative)
    expected_actors = tuple(record.actor_id for record in authoritative)
    expected_labels = tuple(str(record.label) for record in authoritative)
    expected_sentences = tuple(record.sentence_id for record in authoritative)
    if rows != expected_rows:
        raise ValueError(
            "authoritative row IDs must equal the exact eligible partition clips"
        )
    if validated_actors != expected_actors:
        raise ValueError(
            "authoritative row actors do not match eligible split records"
        )
    if tuple(validated_labels.tolist()) != expected_labels:
        raise ValueError(
            "authoritative label sequence does not match eligible split records"
        )
    if (
        not isinstance(sentences, np.ndarray)
        or sentences.ndim != 1
        or sentences.dtype.kind != "U"
        or tuple(sentences.tolist()) != expected_sentences
    ):
        raise ValueError(
            "authoritative sentence sequence does not match eligible split records"
        )
    if (
        not isinstance(features, np.ndarray)
        or features.dtype != np.dtype(np.float64)
        or features.ndim != 2
        or features.shape != (len(rows), 17)
        or not np.isfinite(features).all()
    ):
        raise ValueError("partition feature array shape, dtype, or values are invalid")
    if (
        type(upstream_acoustic_source_commitment_sha256) is not str
        or re.fullmatch(
            r"[0-9A-F]{64}",
            upstream_acoustic_source_commitment_sha256,
        ) is None
    ):
        raise ValueError(
            "upstream acoustic source commitment must be uppercase SHA-256"
        )

    configuration_sha = _canonical_sha256(validated_config)
    environment_sha = _canonical_sha256(validated_environment)
    feature_sha = _canonical_sha256(validated_feature)
    split_schema_sha = _canonical_sha256(validated_split)
    if split_seed_digest != configuration_sha.lower():
        raise ValueError(
            "validated actor split seed does not match configuration commitment"
        )
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
        "label_input_commitment_sha256": _array_commitment(validated_labels),
        "sentence_commitment_sha256": _array_commitment(sentences),
        "feature_input_commitment_sha256": _array_commitment(features),
        "upstream_acoustic_source_commitment_sha256": (
            upstream_acoustic_source_commitment_sha256
        ),
        "model_class_commitment_sha256": _canonical_sha256(
            model_identity_dict
        ),
        "case_count": len(rows),
        "unique_actor_count": len(set(validated_actors)),
    }
    feature_copy = np.asarray(features, dtype=np.float64).copy()
    feature_copy.setflags(write=False)
    state = _PartitionState(
        rows=rows,
        actors=validated_actors,
        labels=expected_labels,
        sentences=expected_sentences,
        features=feature_copy,
        split_assignment=split_assignment,
        configuration=copy.deepcopy(validated_config),
        environment_lock=copy.deepcopy(validated_environment),
        feature_schema=copy.deepcopy(validated_feature),
        split_schema=copy.deepcopy(validated_split),
        model_identity=model_identity_dict,
    )
    evidence = _mint_artifact(PartitionEvidence, payload, state)
    validate_provenance_payload(evidence.to_payload(), expected_role=role)
    return evidence


def _verify_partition_evidence(
    evidence: Any,
    *,
    expected_role: str,
    expected_seed: int | None = None,
) -> PartitionEvidence:
    payload = _verify_artifact_mint(evidence, PartitionEvidence)
    validate_provenance_payload(
        payload,
        expected_role=expected_role,
    )
    links = _artifact_links(evidence)
    if len(links) != 1 or type(links[0]) is not _PartitionState:
        raise ValueError("partition evidence private state is invalid")
    state = links[0]
    reminted = mint_partition_evidence(
        partition_role=expected_role,
        row_ids=state.rows,
        actor_ids=state.actors,
        labels=np.asarray(state.labels, dtype="<U1"),
        sentences=np.asarray(state.sentences, dtype="<U3"),
        features=state.features,
        upstream_acoustic_source_commitment_sha256=payload[
            "upstream_acoustic_source_commitment_sha256"
        ],
        split_assignment=state.split_assignment,
        configuration=state.configuration,
        environment_lock=state.environment_lock,
        feature_schema=state.feature_schema,
        split_schema=state.split_schema,
        model_identity=state.model_identity,
    )
    if (
        reminted.to_payload() != payload
        or reminted.mint_sha256 != evidence.mint_sha256
    ):
        raise ValueError("partition evidence commitment does not match exact inputs")
    if (
        expected_seed is not None
        and state.model_identity["acoustic"]["classifier"]["random_state"]
        != expected_seed
    ):
        raise ValueError("model seed does not match evidence model identity")
    return evidence


def _partition_state(evidence: PartitionEvidence) -> _PartitionState:
    _verify_artifact_mint(evidence, PartitionEvidence)
    links = _artifact_links(evidence)
    if len(links) != 1 or type(links[0]) is not _PartitionState:
        raise ValueError("partition evidence private state is invalid")
    return links[0]


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


def _canonical_parameter(value: Any) -> Any:
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, (list, tuple)):
        return [_canonical_parameter(item) for item in value]
    if isinstance(value, np.ndarray):
        return {
            "array_sha256": _array_commitment(value),
        }
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    return repr(value)


def _estimator_parameters(estimator: object) -> dict[str, Any]:
    return {
        key: _canonical_parameter(value)
        for key, value in sorted(
            estimator.get_params(deep=False).items()
        )
    }


def _classifier_state(classifier: LogisticRegression) -> dict[str, Any]:
    return {
        "classes_sha256": _array_commitment(classifier.classes_),
        "coef_sha256": _array_commitment(classifier.coef_),
        "intercept_sha256": _array_commitment(classifier.intercept_),
        "n_iter_sha256": _array_commitment(classifier.n_iter_),
        "params": _estimator_parameters(classifier),
    }


def _model_state_payload(models: Mapping[str, object]) -> dict[str, Any]:
    if tuple(models) != MODEL_KEYS:
        raise ValueError("fitted model bundle has wrong model order")
    prior = models["class_prior"]
    sentence = models["sentence_id"]
    acoustic = models["acoustic"]
    if (
        type(prior) is not DummyClassifier
        or type(sentence) is not Pipeline
        or type(acoustic) is not Pipeline
    ):
        raise ValueError("fitted model bundle has wrong estimator types")
    one_hot = sentence.named_steps["one_hot"]
    sentence_classifier = sentence.named_steps["classifier"]
    standardizer = acoustic.named_steps["standardize"]
    acoustic_classifier = acoustic.named_steps["classifier"]
    return {
        "class_prior": {
            "params": _estimator_parameters(prior),
            "classes_sha256": _array_commitment(prior.classes_),
            "class_prior_sha256": _array_commitment(prior.class_prior_),
        },
        "sentence_id": {
            "steps": list(sentence.named_steps),
            "categories": [
                [str(value) for value in category.tolist()]
                for category in one_hot.categories_
            ],
            "one_hot_params": _estimator_parameters(one_hot),
            "classifier": _classifier_state(sentence_classifier),
        },
        "acoustic": {
            "steps": list(acoustic.named_steps),
            "mean_sha256": _array_commitment(standardizer.mean_),
            "var_sha256": _array_commitment(standardizer.var_),
            "scale_sha256": _array_commitment(standardizer.scale_),
            "n_samples_seen": int(standardizer.n_samples_seen_),
            "standardizer_params": _estimator_parameters(standardizer),
            "classifier": _classifier_state(acoustic_classifier),
        },
    }


def _verify_fitted_models(
    fitted: Any,
) -> tuple[dict[str, object], _FittedModelState, dict[str, Any]]:
    payload = _verify_artifact_mint(fitted, FittedModelEvidence)
    links = _artifact_links(fitted)
    if len(links) != 1 or type(links[0]) is not _FittedModelState:
        raise ValueError("fitted model private state is invalid")
    state = links[0]
    training = _verify_partition_evidence(
        state.training_evidence,
        expected_role="training_discovery",
        expected_seed=payload["seed"],
    )
    training_state = _partition_state(training)
    models = dict(state.models)
    current_state_sha256 = _canonical_sha256(_model_state_payload(models))
    if (
        current_state_sha256 != state.model_state_sha256
        or current_state_sha256 != payload["model_state_sha256"]
        or training.mint_sha256 != payload["training_evidence_mint_sha256"]
        or training.to_payload() != payload["training_provenance"]
        or training_state.model_identity != payload["model_identity"]
    ):
        raise ValueError("fitted model state or training lineage changed")
    return models, state, payload


def fit_frozen_models(
    evidence: PartitionEvidence,
    seed: int,
) -> FittedModelEvidence:
    bound = _verify_partition_evidence(
        evidence,
        expected_role="training_discovery",
        expected_seed=seed,
    )
    state = _partition_state(bound)
    features = state.features
    sentences = np.asarray(state.sentences, dtype="<U3")
    labels = np.asarray(state.labels, dtype="<U1")
    models = build_models(seed)
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
    model_state_payload = _model_state_payload(models)
    model_state_sha256 = _canonical_sha256(model_state_payload)
    fitted_state = _FittedModelState(
        models=tuple((key, models[key]) for key in MODEL_KEYS),
        model_state_sha256=model_state_sha256,
        training_evidence=bound,
    )
    result = _mint_artifact(
        FittedModelEvidence,
        {
            "schema_id": "emotion-state-phase-b-fitted-model-evidence-v1",
            "model_order": list(MODEL_KEYS),
            "class_order": list(CLASS_ORDER),
            "seed": seed,
            "training_evidence_mint_sha256": bound.mint_sha256,
            "training_provenance": bound.to_payload(),
            "model_identity": copy.deepcopy(state.model_identity),
            "model_state_sha256": model_state_sha256,
            "training_class_counts": {
                label: int(np.count_nonzero(labels == label))
                for label in CLASS_ORDER
            },
        },
        fitted_state,
    )
    _verify_fitted_models(result)
    return result


def predict_probabilities(
    fitted_models: FittedModelEvidence,
    partition_evidence: PartitionEvidence,
) -> ProbabilityEvidence:
    models, fitted_state, fitted_payload = _verify_fitted_models(fitted_models)
    partition_payload = _verify_artifact_mint(
        partition_evidence,
        PartitionEvidence,
    )
    role = validate_partition_role(
        partition_payload["partition_role"],
        (
            "training_discovery",
            "calibration",
            "balanced_diagnostic",
            "final_lockbox",
        ),
    )
    _verify_partition_evidence(partition_evidence, expected_role=role)
    partition_state = _partition_state(partition_evidence)
    if any(
        partition_payload[key]
        != fitted_payload["training_provenance"][key]
        for key in (
            "configuration_sha256",
            "environment_lock_sha256",
            "feature_schema_sha256",
            "split_schema_sha256",
            "split_manifest_sha256",
            "assignment_sha256",
            "model_class_commitment_sha256",
        )
    ):
        raise ValueError("prediction partition and fitted model lineage differ")
    inputs = {
        "class_prior": partition_state.features,
        "sentence_id": np.asarray(
            partition_state.sentences,
            dtype="<U3",
        ).reshape(-1, 1),
        "acoustic": partition_state.features,
    }
    arrays: dict[str, np.ndarray] = {}
    for key in MODEL_KEYS:
        value = np.asarray(
            models[key].predict_proba(inputs[key]),
            dtype=np.float64,
        )
        arrays[key] = value
    validated, row_count = validate_probability_inputs(
        arrays,
        class_order=CLASS_ORDER,
        expected_rows=len(partition_state.rows),
    )
    if row_count != len(partition_state.rows):
        raise ValueError("predicted probability rows do not match partition")
    if (
        _canonical_sha256(_model_state_payload(models))
        != fitted_state.model_state_sha256
    ):
        raise ValueError("fitted model state changed during prediction")
    frozen_arrays: list[tuple[str, np.ndarray]] = []
    for key in MODEL_KEYS:
        copied = validated[key].copy()
        copied.setflags(write=False)
        frozen_arrays.append((key, copied))
    probability_commitment = _canonical_sha256({
        key: _array_commitment(validated[key]) for key in MODEL_KEYS
    })
    state = _ProbabilityState(
        arrays=tuple(frozen_arrays),
        fitted_models=fitted_models,
        partition_evidence=partition_evidence,
    )
    result = _mint_artifact(
        ProbabilityEvidence,
        {
            "schema_id": "emotion-state-phase-b-probability-evidence-v1",
            "partition_role": role,
            "model_order": list(MODEL_KEYS),
            "class_order": list(CLASS_ORDER),
            "case_count": row_count,
            "probability_commitment_sha256": probability_commitment,
            "partition_evidence_mint_sha256": (
                partition_evidence.mint_sha256
            ),
            "provenance": partition_payload,
            "fitted_model_evidence_mint_sha256": fitted_models.mint_sha256,
            "training_evidence_mint_sha256": (
                fitted_payload["training_evidence_mint_sha256"]
            ),
            "training_provenance": fitted_payload["training_provenance"],
            "model_state_sha256": fitted_payload["model_state_sha256"],
        },
        state,
    )
    _verify_probability_evidence(result, expected_role=role)
    return result


def _verify_probability_evidence(
    evidence: Any,
    *,
    expected_role: str | None = None,
) -> tuple[dict[str, np.ndarray], _ProbabilityState, dict[str, Any]]:
    payload = _verify_artifact_mint(evidence, ProbabilityEvidence)
    validate_probability_evidence_payload(
        payload,
        expected_role=expected_role,
    )
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
        raise ValueError(f"ProbabilityEvidence must have {expected_role} role")
    links = _artifact_links(evidence)
    if len(links) != 1 or type(links[0]) is not _ProbabilityState:
        raise ValueError("probability evidence private state is invalid")
    state = links[0]
    models, _, fitted_payload = _verify_fitted_models(state.fitted_models)
    del models
    partition = _verify_partition_evidence(
        state.partition_evidence,
        expected_role=role,
    )
    arrays = dict(state.arrays)
    validated, row_count = validate_probability_inputs(
        arrays,
        class_order=CLASS_ORDER,
        expected_rows=payload["case_count"],
    )
    commitment = _canonical_sha256({
        key: _array_commitment(validated[key]) for key in MODEL_KEYS
    })
    if (
        commitment != payload["probability_commitment_sha256"]
        or partition.mint_sha256 != payload["partition_evidence_mint_sha256"]
        or partition.to_payload() != payload["provenance"]
        or state.fitted_models.mint_sha256
        != payload["fitted_model_evidence_mint_sha256"]
        or fitted_payload["training_evidence_mint_sha256"]
        != payload["training_evidence_mint_sha256"]
        or fitted_payload["training_provenance"]
        != payload["training_provenance"]
        or row_count != payload["case_count"]
    ):
        raise ValueError("probability evidence lineage or commitment changed")
    return validated, state, payload


def _calibrate_probability_arrays(
    probabilities: Mapping[str, np.ndarray],
    targets: Sequence[float],
) -> dict[str, dict[str, dict[str, float]]]:
    if tuple(targets) != COVERAGE_TARGETS:
        raise ValueError("calibration targets must be exactly 1.0, 0.8, 0.6")
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=CLASS_ORDER,
    )
    model_results: dict[str, dict[str, dict[str, float]]] = {}
    for model in MODEL_KEYS:
        confidence = np.max(arrays[model], axis=1)
        candidates = tuple(sorted(set(float(value) for value in confidence)))
        cells: dict[str, dict[str, float]] = {}
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
            cells[str(target)] = {
                "threshold": float(threshold),
                "achieved_coverage": float(achieved),
            }
        model_results[model] = cells
    return model_results


def calibrate_thresholds(
    probabilities: ProbabilityEvidence,
    targets: Sequence[float],
) -> CalibrationEvidence:
    arrays, state, probability_payload = _verify_probability_evidence(
        probabilities,
        expected_role="calibration",
    )
    model_results = _calibrate_probability_arrays(arrays, targets)
    result = {
        "schema_id": "emotion-state-phase-b-calibration-v1",
        "partition_role": "calibration",
        "class_order": list(CLASS_ORDER),
        "targets": list(COVERAGE_TARGETS),
        "models": model_results,
        "probability_evidence_mint_sha256": probabilities.mint_sha256,
        "probability_evidence": probability_payload,
        "provenance": state.partition_evidence.to_payload(),
    }
    result_evidence = _mint_artifact(
        CalibrationEvidence,
        result,
        probabilities,
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


def _verify_calibration_evidence(
    thresholds: Any,
) -> tuple[ProbabilityEvidence, dict[str, Any]]:
    payload = _verify_artifact_mint(thresholds, CalibrationEvidence)
    validate_calibration_result(payload)
    links = _artifact_links(thresholds)
    if len(links) != 1 or type(links[0]) is not ProbabilityEvidence:
        raise ValueError("calibration evidence private lineage is invalid")
    probability = links[0]
    _, state, probability_payload = _verify_probability_evidence(
        probability,
        expected_role="calibration",
    )
    if (
        probability.mint_sha256
        != payload["probability_evidence_mint_sha256"]
        or probability_payload != payload["probability_evidence"]
        or state.partition_evidence.to_payload() != payload["provenance"]
    ):
        raise ValueError("calibration evidence lineage changed")
    return probability, payload


def _shared_probability_lineage_matches(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> bool:
    if any(
        left[key] != right[key]
        for key in (
            "fitted_model_evidence_mint_sha256",
            "training_evidence_mint_sha256",
            "training_provenance",
            "model_state_sha256",
        )
    ):
        return False
    return all(
        left["provenance"][key] == right["provenance"][key]
        for key in (
            "configuration_sha256",
            "environment_lock_sha256",
            "feature_schema_sha256",
            "split_schema_sha256",
            "split_manifest_sha256",
            "assignment_sha256",
            "model_class_commitment_sha256",
        )
    )


def _evaluate_probability_arrays(
    labels: np.ndarray,
    probabilities: Mapping[str, np.ndarray],
    actor_ids: Sequence[str],
    calibration_models: Mapping[str, Any],
) -> dict[str, Any]:
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=CLASS_ORDER,
    )
    validated_labels, actors = validate_labels_and_actors(
        labels,
        actor_ids,
        expected_rows=row_count,
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
        retained_cells: dict[str, Any] = {}
        for target in COVERAGE_TARGETS:
            target_key = str(target)
            calibration_cell = calibration_models[model][target_key]
            threshold = calibration_cell["threshold"]
            mask = confidence >= threshold
            retained_actors = _actor_count(actors, mask)
            retained_cases = int(np.count_nonzero(mask))
            retained_suppressed = (
                retained_actors < MINIMUM_UNIQUE_ACTORS
                or retained_cases == 0
            )
            retained_cells[target_key] = {
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
    return model_results


def evaluate_partition(
    probabilities: ProbabilityEvidence,
    thresholds: CalibrationEvidence,
) -> EvaluationEvidence:
    arrays, probability_state, probability_payload = (
        _verify_probability_evidence(probabilities)
    )
    role = validate_partition_role(
        probability_payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    _, calibration_payload = _verify_calibration_evidence(thresholds)
    calibration_probability_payload = calibration_payload[
        "probability_evidence"
    ]
    if not _shared_probability_lineage_matches(
        probability_payload,
        calibration_probability_payload,
    ):
        raise ValueError(
            "calibration lineage does not match evaluated model/training lineage"
        )
    partition_state = _partition_state(
        probability_state.partition_evidence
    )
    labels = np.asarray(partition_state.labels, dtype="<U1")
    actors = partition_state.actors
    model_results = _evaluate_probability_arrays(
        labels,
        arrays,
        actors,
        calibration_payload["models"],
    )
    result = {
        "schema_id": "emotion-state-phase-b-evaluation-v1",
        "partition_role": role,
        "class_order": list(CLASS_ORDER),
        "models": model_results,
        "final_decision_eligible": role == "final_lockbox",
        "probability_evidence_mint_sha256": probabilities.mint_sha256,
        "probability_evidence": probability_payload,
        "calibration_evidence_mint_sha256": thresholds.mint_sha256,
        "calibration_evidence": calibration_payload,
        "provenance": probability_state.partition_evidence.to_payload(),
    }
    result_evidence = _mint_artifact(
        EvaluationEvidence,
        result,
        probabilities,
        thresholds,
    )
    validate_evaluation_result(
        result_evidence.to_payload(),
        expected_role=role,
    )
    return result_evidence


def _paired_actor_bootstrap_arrays(
    labels: np.ndarray,
    probabilities: Mapping[str, np.ndarray],
    actor_ids: Sequence[str],
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    if type(resamples) is not int or resamples != BOOTSTRAP_RESAMPLES:
        raise ValueError("paired actor bootstrap requires exactly 2,000 resamples")
    if type(seed) is not int or seed < 0:
        raise ValueError("paired actor bootstrap seed must be non-negative")
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
    return intervals


def paired_actor_bootstrap(
    probabilities: ProbabilityEvidence,
    resamples: int,
    seed: int,
) -> BootstrapEvidence:
    arrays, probability_state, probability_payload = (
        _verify_probability_evidence(
            probabilities,
            expected_role="final_lockbox",
        )
    )
    partition_state = _partition_state(
        probability_state.partition_evidence
    )
    configuration_sha256 = probability_payload["provenance"][
        "configuration_sha256"
    ]
    if (
        type(seed) is not int
        or seed != int(configuration_sha256[:16], 16)
    ):
        raise ValueError(
            "bootstrap seed must derive from the configuration SHA-256"
        )
    labels = np.asarray(partition_state.labels, dtype="<U1")
    intervals = _paired_actor_bootstrap_arrays(
        labels,
        arrays,
        partition_state.actors,
        resamples,
        seed,
    )
    result = {
        "schema_id": "emotion-state-phase-b-bootstrap-v1",
        "partition_role": "final_lockbox",
        "class_order": list(CLASS_ORDER),
        "resamples": resamples,
        "seed": seed,
        "configuration_sha256": configuration_sha256,
        "unique_actor_count": len(set(partition_state.actors)),
        "case_count": len(partition_state.rows),
        "paired_macro_f1_lift": intervals,
        "probability_evidence_mint_sha256": probabilities.mint_sha256,
        "probability_evidence": probability_payload,
        "provenance": probability_state.partition_evidence.to_payload(),
    }
    result_evidence = _mint_artifact(
        BootstrapEvidence,
        result,
        probabilities,
    )
    validate_bootstrap_result(result_evidence.to_payload())
    return result_evidence


SLICE_INSTABILITY_TOLERANCE = 0.10


def _verify_evaluation_evidence(
    evaluation: Any,
    *,
    expected_role: str | None = None,
) -> tuple[ProbabilityEvidence, CalibrationEvidence, dict[str, Any]]:
    payload = _verify_artifact_mint(evaluation, EvaluationEvidence)
    validate_evaluation_result(payload, expected_role=expected_role)
    links = _artifact_links(evaluation)
    if (
        len(links) != 2
        or type(links[0]) is not ProbabilityEvidence
        or type(links[1]) is not CalibrationEvidence
    ):
        raise ValueError("evaluation evidence private lineage is invalid")
    probability, calibration = links
    _, _, probability_payload = _verify_probability_evidence(probability)
    _, calibration_payload = _verify_calibration_evidence(calibration)
    if (
        probability.mint_sha256
        != payload["probability_evidence_mint_sha256"]
        or probability_payload != payload["probability_evidence"]
        or calibration.mint_sha256
        != payload["calibration_evidence_mint_sha256"]
        or calibration_payload != payload["calibration_evidence"]
    ):
        raise ValueError("evaluation evidence lineage changed")
    return probability, calibration, payload


def _verify_bootstrap_evidence(
    bootstrap: Any,
) -> tuple[ProbabilityEvidence, dict[str, Any]]:
    payload = _verify_artifact_mint(bootstrap, BootstrapEvidence)
    validate_bootstrap_result(payload)
    links = _artifact_links(bootstrap)
    if len(links) != 1 or type(links[0]) is not ProbabilityEvidence:
        raise ValueError("bootstrap evidence private lineage is invalid")
    probability = links[0]
    _, _, probability_payload = _verify_probability_evidence(
        probability,
        expected_role="final_lockbox",
    )
    if (
        probability.mint_sha256
        != payload["probability_evidence_mint_sha256"]
        or probability_payload != payload["probability_evidence"]
    ):
        raise ValueError("bootstrap evidence lineage changed")
    return probability, payload


def mint_slice_analysis(
    probabilities: ProbabilityEvidence,
    evaluation: EvaluationEvidence,
    slices: Mapping[str, Sequence[str]],
) -> SliceAnalysisEvidence:
    arrays, probability_state, probability_payload = (
        _verify_probability_evidence(probabilities)
    )
    role = validate_partition_role(
        probability_payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    evaluation_probability, _, evaluation_payload = (
        _verify_evaluation_evidence(evaluation, expected_role=role)
    )
    if evaluation_probability.mint_sha256 != probabilities.mint_sha256:
        raise ValueError("slice analysis and evaluation probability lineage differ")
    if not isinstance(slices, Mapping) or not slices:
        raise ValueError("slice contributors must be a non-empty mapping")
    partition_state = _partition_state(
        probability_state.partition_evidence
    )
    row_index = {
        row_id: index for index, row_id in enumerate(partition_state.rows)
    }
    labels = np.asarray(partition_state.labels, dtype="<U1")
    full_lifts = {
        baseline: (
            evaluation_payload["models"]["acoustic"]["macro_f1"]
            - evaluation_payload["models"][baseline]["macro_f1"]
        )
        for baseline in ("class_prior", "sentence_id")
    }
    cells: dict[str, Any] = {}
    reversal = False
    instability = False
    for name, contributors in sorted(slices.items()):
        if (
            type(name) is not str
            or not name
            or name.strip() != name
            or isinstance(contributors, (str, bytes))
        ):
            raise ValueError("slice contributors and names are invalid")
        try:
            contributor_rows = tuple(contributors)
        except TypeError as error:
            raise ValueError("slice contributors must be row-ID sequences") from error
        if (
            len(contributor_rows) != len(set(contributor_rows))
            or any(
                type(row) is not str or row not in row_index
                for row in contributor_rows
            )
        ):
            raise ValueError("slice contributors must be unique authoritative rows")
        indexes = np.asarray(
            [row_index[row] for row in contributor_rows],
            dtype=np.int64,
        )
        contributor_actors = tuple(
            partition_state.actors[index] for index in indexes.tolist()
        )
        actor_count = len(set(contributor_actors))
        suppressed = actor_count < MINIMUM_UNIQUE_ACTORS
        scores = None
        lifts = None
        if not suppressed:
            scores = {
                model: _macro_f1(
                    labels[indexes],
                    _predicted_labels(arrays[model][indexes]),
                )
                for model in MODEL_KEYS
            }
            lifts = {
                baseline: scores["acoustic"] - scores[baseline]
                for baseline in ("class_prior", "sentence_id")
            }
            reversal = reversal or any(value < 0.0 for value in lifts.values())
            instability = instability or any(
                abs(lifts[baseline] - full_lifts[baseline])
                > SLICE_INSTABILITY_TOLERANCE
                for baseline in lifts
            )
        cells[name] = {
            "case_count": len(contributor_rows),
            "unique_actor_count": actor_count,
            "suppressed": suppressed,
            "contributor_row_commitment_sha256": _canonical_sha256(
                list(contributor_rows)
            ),
            "contributor_actor_commitment_sha256": _canonical_sha256(
                list(contributor_actors)
            ),
            "model_macro_f1": scores,
            "paired_macro_f1_lift": lifts,
        }
    result = _mint_artifact(
        SliceAnalysisEvidence,
        {
            "schema_id": "emotion-state-phase-b-slice-analysis-v2",
            "partition_role": role,
            "class_order": list(CLASS_ORDER),
            "instability_tolerance": SLICE_INSTABILITY_TOLERANCE,
            "slices": cells,
            "eligible_slice_reversal": reversal,
            "eligible_slice_instability": instability,
            "probability_evidence_mint_sha256": probabilities.mint_sha256,
            "evaluation_evidence_mint_sha256": evaluation.mint_sha256,
            "provenance": probability_state.partition_evidence.to_payload(),
        },
        probabilities,
        evaluation,
    )
    _verify_slice_analysis(result, expected_role=role)
    return result


def _verify_slice_analysis(
    analysis: Any,
    *,
    expected_role: str | None = None,
) -> tuple[ProbabilityEvidence, EvaluationEvidence, dict[str, Any]]:
    payload = _verify_artifact_mint(analysis, SliceAnalysisEvidence)
    role = validate_partition_role(
        payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    if expected_role is not None and role != expected_role:
        raise ValueError(f"slice analysis must have {expected_role} role")
    if payload["schema_id"] != "emotion-state-phase-b-slice-analysis-v2":
        raise ValueError("slice analysis schema does not match")
    if payload["instability_tolerance"] != SLICE_INSTABILITY_TOLERANCE:
        raise ValueError("slice analysis instability tolerance does not match")
    if (
        type(payload["eligible_slice_reversal"]) is not bool
        or type(payload["eligible_slice_instability"]) is not bool
        or not isinstance(payload["slices"], Mapping)
        or not payload["slices"]
    ):
        raise ValueError("slice analysis derived fields are invalid")
    links = _artifact_links(analysis)
    if (
        len(links) != 2
        or type(links[0]) is not ProbabilityEvidence
        or type(links[1]) is not EvaluationEvidence
    ):
        raise ValueError("slice analysis private lineage is invalid")
    probability, evaluation = links
    _, probability_state, probability_payload = _verify_probability_evidence(
        probability,
        expected_role=role,
    )
    evaluation_probability, _, evaluation_payload = (
        _verify_evaluation_evidence(evaluation, expected_role=role)
    )
    if (
        probability.mint_sha256
        != payload["probability_evidence_mint_sha256"]
        or evaluation.mint_sha256
        != payload["evaluation_evidence_mint_sha256"]
        or evaluation_probability.mint_sha256 != probability.mint_sha256
        or probability_state.partition_evidence.to_payload()
        != payload["provenance"]
    ):
        raise ValueError("slice analysis provenance commitments do not match")
    full_lifts = {
        baseline: (
            evaluation_payload["models"]["acoustic"]["macro_f1"]
            - evaluation_payload["models"][baseline]["macro_f1"]
        )
        for baseline in ("class_prior", "sentence_id")
    }
    derived_reversal = False
    derived_instability = False
    for name, cell in payload["slices"].items():
        if type(name) is not str or not name:
            raise ValueError("slice name is invalid")
        if set(cell) != {
            "case_count",
            "unique_actor_count",
            "suppressed",
            "contributor_row_commitment_sha256",
            "contributor_actor_commitment_sha256",
            "model_macro_f1",
            "paired_macro_f1_lift",
        }:
            raise ValueError("slice analytical cell schema is invalid")
        if (
            type(cell["case_count"]) is not int
            or cell["case_count"] < 0
            or type(cell["unique_actor_count"]) is not int
            or cell["unique_actor_count"] < 0
            or cell["unique_actor_count"] > cell["case_count"]
            or type(cell["suppressed"]) is not bool
        ):
            raise ValueError("slice contributor counts are invalid")
        for digest_key in (
            "contributor_row_commitment_sha256",
            "contributor_actor_commitment_sha256",
        ):
            if (
                type(cell[digest_key]) is not str
                or re.fullmatch(r"[0-9A-F]{64}", cell[digest_key]) is None
            ):
                raise ValueError("slice contributor commitment is invalid")
        suppressed = cell["suppressed"]
        if suppressed is not (cell["unique_actor_count"] < MINIMUM_UNIQUE_ACTORS):
            raise ValueError("slice suppression contradicts contributor count")
        if suppressed:
            if (
                cell["model_macro_f1"] is not None
                or cell["paired_macro_f1_lift"] is not None
            ):
                raise ValueError("suppressed slice metrics must be null")
            continue
        if type(cell["model_macro_f1"]) is not dict or set(
            cell["model_macro_f1"]
        ) != set(MODEL_KEYS):
            raise ValueError("slice model metrics are invalid")
        for value in cell["model_macro_f1"].values():
            if type(value) is not float or not 0.0 <= value <= 1.0:
                raise ValueError("slice macro-F1 is invalid")
        if type(cell["paired_macro_f1_lift"]) is not dict or set(
            cell["paired_macro_f1_lift"]
        ) != {
            "class_prior",
            "sentence_id",
        }:
            raise ValueError("slice lift metrics are invalid")
        for baseline, value in cell["paired_macro_f1_lift"].items():
            expected_lift = (
                cell["model_macro_f1"]["acoustic"]
                - cell["model_macro_f1"][baseline]
            )
            if (
                type(value) is not float
                or not -1.0 <= value <= 1.0
                or not math.isclose(
                    value,
                    expected_lift,
                    rel_tol=0.0,
                    abs_tol=1e-15,
                )
            ):
                raise ValueError("slice lift metric is invalid")
            derived_reversal = derived_reversal or value < 0.0
            derived_instability = derived_instability or (
                abs(value - full_lifts[baseline])
                > SLICE_INSTABILITY_TOLERANCE
            )
    if (
        payload["eligible_slice_reversal"] is not derived_reversal
        or payload["eligible_slice_instability"] is not derived_instability
    ):
        raise ValueError("slice analytical flags are not derived from metrics")
    del probability_payload
    return probability, evaluation, payload


def _derived_confidence_abstention(models: Mapping[str, Any]) -> bool:
    acoustic = models["acoustic"]
    candidates = [
        acoustic["retained"][key]
        for key in ("0.8", "0.6")
        if (
            not acoustic["retained"][key]["suppressed"]
            and acoustic["retained"][key]["coverage"] < 1.0
        )
    ]
    return (
        bool(candidates)
        and any(
            cell["retained_macro_f1"] > acoustic["macro_f1"]
            for cell in candidates
        )
        and all(
            cell["retained_macro_f1"] >= acoustic["macro_f1"]
            for cell in candidates
        )
    )


def build_decision_evidence(
    evaluation: EvaluationEvidence,
    bootstrap: BootstrapEvidence,
    slice_analysis: SliceAnalysisEvidence,
) -> DecisionEvidence:
    evaluation_probability, calibration, validated_evaluation = (
        _verify_evaluation_evidence(
            evaluation,
            expected_role="final_lockbox",
        )
    )
    bootstrap_probability, validated_bootstrap = (
        _verify_bootstrap_evidence(bootstrap)
    )
    slice_probability, slice_evaluation, validated_slice = (
        _verify_slice_analysis(
            slice_analysis,
            expected_role="final_lockbox",
        )
    )
    if (
        evaluation_probability.mint_sha256
        != bootstrap_probability.mint_sha256
        or evaluation_probability.mint_sha256
        != slice_probability.mint_sha256
        or slice_evaluation.mint_sha256 != evaluation.mint_sha256
        or validated_evaluation["provenance"]
        != validated_bootstrap["provenance"]
        or validated_evaluation["probability_evidence"]
        != validated_bootstrap["probability_evidence"]
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
    models = validated_evaluation["models"]
    lifts = validated_bootstrap["paired_macro_f1_lift"]
    sentence_driven_apparent_lift = (
        models["sentence_id"]["macro_f1"]
        > models["class_prior"]["macro_f1"]
        and lifts["sentence_id"]["point_estimate"] <= 0.0
    )
    confidence_abstention_improves = _derived_confidence_abstention(models)
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
        "eligible_slice_reversal": validated_slice[
            "eligible_slice_reversal"
        ],
        "eligible_slice_instability": validated_slice[
            "eligible_slice_instability"
        ],
        "confidence_abstention_improves": confidence_abstention_improves,
        "evaluation_evidence_mint_sha256": evaluation.mint_sha256,
        "bootstrap_evidence_mint_sha256": bootstrap.mint_sha256,
        "slice_analysis_mint_sha256": slice_analysis.mint_sha256,
        "calibration_evidence_mint_sha256": calibration.mint_sha256,
        "calibration_evidence": calibration.to_payload(),
        "provenance": validated_evaluation["provenance"],
    }
    all_valid = {
        "material_valid": True,
        "environment_valid": True,
        "split_valid": True,
        "leakage_free": True,
        "deterministic": True,
        "lockbox_valid": True,
    }
    result_evidence = _mint_artifact(
        DecisionEvidence,
        result,
        evaluation,
        bootstrap,
        slice_analysis,
    )
    validate_decision_inputs(result_evidence.to_payload(), all_valid)
    return result_evidence


def _decision_outcome(
    validated_metrics: Mapping[str, Any],
    validated_validity: Mapping[str, bool],
) -> str:
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


def decide_experiment(
    metrics: DecisionEvidence,
    validity: Mapping[str, bool],
) -> str:
    payload = _verify_artifact_mint(metrics, DecisionEvidence)
    links = _artifact_links(metrics)
    if (
        len(links) != 3
        or type(links[0]) is not EvaluationEvidence
        or type(links[1]) is not BootstrapEvidence
        or type(links[2]) is not SliceAnalysisEvidence
    ):
        raise ValueError("bound decision evidence private lineage is invalid")
    evaluation, bootstrap, slice_analysis = links
    _, calibration, evaluation_payload = _verify_evaluation_evidence(
        evaluation,
        expected_role="final_lockbox",
    )
    _, bootstrap_payload = _verify_bootstrap_evidence(bootstrap)
    _, _, slice_payload = _verify_slice_analysis(
        slice_analysis,
        expected_role="final_lockbox",
    )
    expected_fields = {
        "models": evaluation_payload["models"],
        "paired_macro_f1_lift": bootstrap_payload[
            "paired_macro_f1_lift"
        ],
        "sentence_driven_apparent_lift": (
            evaluation_payload["models"]["sentence_id"]["macro_f1"]
            > evaluation_payload["models"]["class_prior"]["macro_f1"]
            and bootstrap_payload["paired_macro_f1_lift"]["sentence_id"][
                "point_estimate"
            ] <= 0.0
        ),
        "eligible_slice_reversal": slice_payload[
            "eligible_slice_reversal"
        ],
        "eligible_slice_instability": slice_payload[
            "eligible_slice_instability"
        ],
        "confidence_abstention_improves": _derived_confidence_abstention(
            evaluation_payload["models"]
        ),
        "evaluation_evidence_mint_sha256": evaluation.mint_sha256,
        "bootstrap_evidence_mint_sha256": bootstrap.mint_sha256,
        "slice_analysis_mint_sha256": slice_analysis.mint_sha256,
        "calibration_evidence_mint_sha256": calibration.mint_sha256,
        "calibration_evidence": calibration.to_payload(),
        "provenance": evaluation_payload["provenance"],
    }
    if any(payload[key] != value for key, value in expected_fields.items()):
        raise ValueError("bound decision evidence derived lineage changed")
    validated_metrics, validated_validity = validate_decision_inputs(
        payload,
        validity,
    )
    return _decision_outcome(validated_metrics, validated_validity)
