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
