from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from collections import Counter, defaultdict
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
