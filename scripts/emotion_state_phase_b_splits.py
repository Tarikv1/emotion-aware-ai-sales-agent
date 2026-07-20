"""Deterministic actor split using only reference labels and scripted sentences."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from scripts.emotion_state_phase_b_evaluation import CremaLabelRecord
from scripts.validate_emotion_state_002_phase_b import (
    ACTOR_SPLIT_SUMMARY_SCHEMA_ID,
    EXPECTED_CONFIG,
    EXPECTED_SPLIT_SCHEMA,
    validate_actor_split_summary,
)

LABEL_ORDER = ("A", "D", "F", "H", "N", "S")
PARTITION_ORDER = tuple(EXPECTED_SPLIT_SCHEMA["partition_order"])
PARTITION_CAPACITIES = dict(EXPECTED_SPLIT_SCHEMA["partition_actor_counts"])
DEPENDENCY_ROLES = dict(EXPECTED_SPLIT_SCHEMA["dependency_roles"])
EXPECTED_ACTOR_COUNT = EXPECTED_SPLIT_SCHEMA["expected_actor_count"]
EXPECTED_SENTENCE_COUNT = EXPECTED_SPLIT_SCHEMA["expected_sentence_count"]
SEED_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ACTOR_ID_PATTERN = re.compile(r"^\d{4}$")
SENTENCE_ID_PATTERN = re.compile(r"^[A-Z0-9]{3}$")


def _canonical_digest(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def _validated_records(
    records: Sequence[CremaLabelRecord],
) -> tuple[tuple[CremaLabelRecord, ...], tuple[str, ...], tuple[str, ...]]:
    try:
        materialized = tuple(records)
    except TypeError as error:
        raise ValueError("actor split records must be a sequence") from error
    if not materialized:
        raise ValueError("actor split records must be non-empty")

    clip_stems: set[str] = set()
    actors: set[str] = set()
    sentences: set[str] = set()
    labels: set[str] = set()
    for record in materialized:
        if not isinstance(record, CremaLabelRecord):
            raise ValueError("actor split records must be CremaLabelRecord objects")
        if (
            not isinstance(record.clip_stem, str)
            or not record.clip_stem
            or record.clip_stem in clip_stems
        ):
            raise ValueError("actor split clip identities must be unique strings")
        if (
            not isinstance(record.actor_id, str)
            or ACTOR_ID_PATTERN.fullmatch(record.actor_id) is None
        ):
            raise ValueError("actor split actor identifiers must be four digits")
        if (
            not isinstance(record.sentence_id, str)
            or SENTENCE_ID_PATTERN.fullmatch(record.sentence_id) is None
        ):
            raise ValueError(
                "actor split sentence identifiers must be three uppercase characters"
            )
        if (
            not isinstance(record.label, str)
            or record.label not in LABEL_ORDER
            or record.abstention_reason is not None
        ):
            raise ValueError("actor split records must be eligible six-label records")
        clip_stems.add(record.clip_stem)
        actors.add(record.actor_id)
        sentences.add(record.sentence_id)
        labels.add(record.label)

    if len(actors) != EXPECTED_ACTOR_COUNT:
        raise ValueError("actor split requires exactly 91 actors")
    if len(sentences) != EXPECTED_SENTENCE_COUNT:
        raise ValueError("actor split requires exactly 12 sentences")
    if labels != set(LABEL_ORDER):
        raise ValueError("actor split requires all six labels")
    return materialized, tuple(sorted(actors)), tuple(sorted(sentences))


def _validated_assignment(
    actors: tuple[str, ...],
    assignment: Mapping[str, str],
) -> dict[str, str]:
    if not isinstance(assignment, Mapping):
        raise ValueError("actor split assignment must be a mapping")
    if any(
        not isinstance(actor_id, str) or not isinstance(partition, str)
        for actor_id, partition in assignment.items()
    ):
        raise ValueError("actor split assignment entries must be strings")
    if set(assignment) != set(actors):
        raise ValueError("actor split assignment must be exhaustive")
    if any(partition not in PARTITION_ORDER for partition in assignment.values()):
        raise ValueError("actor split assignment contains an unknown partition")
    return {actor_id: assignment[actor_id] for actor_id in actors}


def _actor_vectors(
    records: tuple[CremaLabelRecord, ...],
    actors: tuple[str, ...],
    sentences: tuple[str, ...],
) -> tuple[dict[str, list[int]], list[int]]:
    vector_size = len(LABEL_ORDER) + len(sentences)
    label_offsets = {label: index for index, label in enumerate(LABEL_ORDER)}
    sentence_offsets = {
        sentence: len(LABEL_ORDER) + index
        for index, sentence in enumerate(sentences)
    }
    vectors = {actor_id: [0] * vector_size for actor_id in actors}
    for record in records:
        vector = vectors[record.actor_id]
        vector[label_offsets[record.label]] += 1
        vector[sentence_offsets[record.sentence_id]] += 1
    global_vector = [
        sum(vector[index] for vector in vectors.values())
        for index in range(vector_size)
    ]
    return vectors, global_vector


def build_actor_split(
    records: Sequence[CremaLabelRecord],
    seed_digest: str,
) -> dict[str, str]:
    if (
        not isinstance(seed_digest, str)
        or SEED_DIGEST_PATTERN.fullmatch(seed_digest) is None
    ):
        raise ValueError("actor split seed digest must be lowercase SHA-256")
    materialized, actors, sentences = _validated_records(records)
    vectors, global_vector = _actor_vectors(materialized, actors, sentences)
    actor_order = sorted(
        actors,
        key=lambda actor_id: (
            -math.sqrt(sum(value * value for value in vectors[actor_id])),
            hashlib.sha256(
                f"{seed_digest}:{actor_id}".encode("utf-8")
            ).hexdigest(),
        ),
    )
    partition_vectors = {
        partition: [0] * len(global_vector) for partition in PARTITION_ORDER
    }
    partition_actor_counts: Counter[str] = Counter()
    assignment: dict[str, str] = {}
    for actor_id in actor_order:
        actor_vector = vectors[actor_id]
        candidates: list[tuple[float, int, str, list[int]]] = []
        for partition_index, partition in enumerate(PARTITION_ORDER):
            if (
                partition_actor_counts[partition]
                >= PARTITION_CAPACITIES[partition]
            ):
                continue
            candidate_actor_count = partition_actor_counts[partition] + 1
            candidate_vector = [
                current + added
                for current, added in zip(
                    partition_vectors[partition],
                    actor_vector,
                )
            ]
            score = sum(
                (
                    candidate
                    - global_value
                    * candidate_actor_count
                    / EXPECTED_ACTOR_COUNT
                ) ** 2
                for candidate, global_value in zip(
                    candidate_vector,
                    global_vector,
                )
            )
            candidates.append(
                (score, partition_index, partition, candidate_vector)
            )
        if not candidates:
            raise ValueError("actor split capacities were exhausted")
        _, _, selected_partition, selected_vector = min(
            candidates,
            key=lambda candidate: (candidate[0], candidate[1]),
        )
        assignment[actor_id] = selected_partition
        partition_actor_counts[selected_partition] += 1
        partition_vectors[selected_partition] = selected_vector

    canonical_assignment = {
        actor_id: assignment[actor_id] for actor_id in actors
    }
    validate_actor_split(materialized, canonical_assignment)
    return canonical_assignment


def validate_actor_split(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
) -> dict[str, Any]:
    materialized, actors, _ = _validated_records(records)
    canonical_assignment = _validated_assignment(actors, assignment)
    actor_counts = Counter(canonical_assignment.values())
    if dict(actor_counts) != PARTITION_CAPACITIES:
        raise ValueError("actor split partition actor capacities do not match")

    partition_records: dict[str, list[CremaLabelRecord]] = defaultdict(list)
    for record in materialized:
        partition_records[canonical_assignment[record.actor_id]].append(record)

    partition_record_counts: dict[str, int] = {}
    partition_label_presence_counts: dict[str, int] = {}
    partition_sentence_presence_counts: dict[str, int] = {}
    for partition in PARTITION_ORDER:
        records_in_partition = partition_records[partition]
        label_count = len({record.label for record in records_in_partition})
        sentence_count = len({
            record.sentence_id for record in records_in_partition
        })
        if label_count != len(LABEL_ORDER):
            raise ValueError(
                f"actor split partition {partition} is missing a required label"
            )
        if sentence_count != EXPECTED_SENTENCE_COUNT:
            raise ValueError(
                f"actor split partition {partition} is missing a required sentence"
            )
        partition_record_counts[partition] = len(records_in_partition)
        partition_label_presence_counts[partition] = label_count
        partition_sentence_presence_counts[partition] = sentence_count

    summary: dict[str, Any] = {
        "schema_id": ACTOR_SPLIT_SUMMARY_SCHEMA_ID,
        "schema_version": 1,
        "dataset_id": EXPECTED_SPLIT_SCHEMA["dataset_id"],
        "split_schema_id": EXPECTED_SPLIT_SCHEMA["schema_id"],
        "dependency_roles": dict(DEPENDENCY_ROLES),
        "partition_order": list(PARTITION_ORDER),
        "partition_actor_counts": {
            partition: actor_counts[partition] for partition in PARTITION_ORDER
        },
        "partition_record_counts": partition_record_counts,
        "partition_label_presence_counts": partition_label_presence_counts,
        "partition_sentence_presence_counts": (
            partition_sentence_presence_counts
        ),
        "eligible_record_count": len(materialized),
        "eligible_actor_count": len(actors),
        "eligible_sentence_count": EXPECTED_SENTENCE_COUNT,
        "eligible_label_count": len(LABEL_ORDER),
        "actor_exclusivity_validated": True,
    }
    return validate_actor_split_summary(summary)


def split_manifest_digest(
    records: Sequence[CremaLabelRecord],
    assignment: Mapping[str, str],
) -> str:
    materialized, actors, _ = _validated_records(records)
    canonical_assignment = _validated_assignment(actors, assignment)
    assignment_commitment = _canonical_digest([
        [actor_id, canonical_assignment[actor_id]] for actor_id in actors
    ])
    actor_counts = Counter(canonical_assignment.values())
    record_counts: Counter[str] = Counter(
        canonical_assignment[record.actor_id] for record in materialized
    )
    tracked_digest_payload = {
        "schema_id": "emotion-state-actor-split-manifest-commitment-v1",
        "schema_version": 1,
        "checkpoint_id": EXPECTED_CONFIG["checkpoint_id"],
        "split_schema_id": EXPECTED_SPLIT_SCHEMA["schema_id"],
        "assignment_sha256": assignment_commitment,
        "partition_actor_counts": {
            partition: actor_counts[partition] for partition in PARTITION_ORDER
        },
        "partition_record_counts": {
            partition: record_counts[partition] for partition in PARTITION_ORDER
        },
    }
    return _canonical_digest(tracked_digest_payload)
