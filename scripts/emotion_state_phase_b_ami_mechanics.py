from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


PARTITION_CELLS = ("scenario_only", "full_corpus", "full_only")
BUCKET_VALUE_KEYS = (
    "turn_duration_median_ms",
    "turn_duration_p90_ms",
    "inter_turn_gap_median_ms",
    "inter_turn_gap_p90_ms",
)
SCALAR_VALUE_KEYS = (
    "overlap_ratio",
    "floor_changes_per_minute",
    "normalized_speaker_entropy",
    "backchannels_per_100_turns",
)
VALUE_KEYS = BUCKET_VALUE_KEYS + SCALAR_VALUE_KEYS
BACKCHANNEL_ACT = "backchannel"
_REFERENCE_FRAGMENT = re.compile(
    r"^id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?$"
)


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


@dataclass(frozen=True)
class _Boundary:
    meeting_id: str
    agent: str
    start_ms: int
    end_ms: int


def _normalized_name(name: str) -> str:
    local_name = name.rsplit("}", 1)[-1].split(":")[-1].lower()
    return re.sub(r"[^a-z0-9]", "", local_name)


def _attribute(element: ET.Element, *names: str) -> str | None:
    expected = {_normalized_name(name) for name in names}
    values = [
        value.strip()
        for key, value in element.attrib.items()
        if _normalized_name(key) in expected and value.strip()
    ]
    if not values:
        return None
    if len(set(values)) != 1:
        raise ValueError("conflicting namespace-normalized XML attributes")
    return values[0]


def _xml(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise ValueError(f"AMI XML is unreadable: {path.name}") from error


def _nonempty_identifiers(
    values: Sequence[str],
    name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    normalized = tuple(values)
    if (
        not normalized
        or any(type(value) is not str or not value.strip() for value in normalized)
        or len(set(normalized)) != len(normalized)
    ):
        raise ValueError(f"{name} must contain unique non-empty identifiers")
    return normalized


def _milliseconds(value: str | None) -> int:
    if value is None:
        raise ValueError("AMI word time span is incomplete")
    try:
        milliseconds = Decimal(value) * 1000
    except InvalidOperation as error:
        raise ValueError("AMI word time span is malformed") from error
    if not milliseconds.is_finite() or milliseconds != milliseconds.to_integral():
        raise ValueError("AMI word time span must use integral milliseconds")
    return int(milliseconds)


def _source_identity(path: Path, root: ET.Element) -> tuple[str, str]:
    meeting_id = _attribute(root, "meeting_id", "meeting", "observation")
    agent = _attribute(root, "agent", "speaker", "participant", "channel")
    parts = path.name.split(".")
    if meeting_id is None and len(parts) >= 3:
        meeting_id = parts[0]
    if agent is None and len(parts) >= 3:
        agent = parts[1]
    if meeting_id is None or agent is None:
        raise ValueError("AMI annotation source identity is incomplete")
    return meeting_id, agent


def _local_reference(
    href: str | None,
    current_filename: str,
) -> tuple[str, str, str | None]:
    if href is None or href.count("#") != 1:
        raise ValueError("AMI NXT reference is malformed")
    target, fragment = href.split("#", 1)
    target = target.strip()
    if not target:
        target = current_filename
    if (
        "://" in target
        or target.startswith(("/", "\\"))
        or "\\" in target
        or "/" in target
        or ":" in target
        or target in {".", ".."}
    ):
        raise ValueError("AMI NXT reference uses an external URI")
    match = _REFERENCE_FRAGMENT.fullmatch(fragment.strip())
    if match is None:
        raise ValueError("AMI NXT reference fragment is malformed")
    return target, match.group(1), match.group(2)


def _resolve_range(
    target: str,
    first_id: str,
    last_id: str | None,
    items: Mapping[str, tuple[_Boundary, ...]],
    identifiers: Mapping[str, Mapping[str, int]],
    kind: str,
) -> tuple[_Boundary, ...]:
    if target not in items or target not in identifiers:
        raise ValueError(f"AMI NXT reference targets an unknown local {kind} file")
    positions = identifiers[target]
    if first_id not in positions or (last_id is not None and last_id not in positions):
        raise ValueError(f"AMI NXT reference targets an unknown local {kind}")
    first = positions[first_id]
    last = first if last_id is None else positions[last_id]
    if first > last:
        raise ValueError(f"AMI NXT {kind} range is reversed")
    return items[target][first:last + 1]


def _merge_boundaries(boundaries: Sequence[_Boundary]) -> _Boundary:
    if not boundaries:
        raise ValueError("AMI NXT reference resolves to no timing boundaries")
    identities = {(item.meeting_id, item.agent) for item in boundaries}
    if len(identities) != 1:
        raise ValueError("AMI NXT reference crosses meeting or participant")
    meeting_id, agent = next(iter(identities))
    start_ms = min(item.start_ms for item in boundaries)
    end_ms = max(item.end_ms for item in boundaries)
    if not 0 <= start_ms < end_ms:
        raise ValueError("AMI resolved time span is malformed")
    return _Boundary(meeting_id, agent, start_ms, end_ms)


def _metadata_dependencies(
    path: Path,
    known_meetings: set[str],
) -> dict[tuple[str, str], str]:
    dependencies: dict[tuple[str, str], str] = {}
    for meeting in _xml(path).iter():
        if _normalized_name(meeting.tag) != "meeting":
            continue
        meeting_id = _attribute(meeting, "id", "meeting_id", "observation")
        if meeting_id is None or meeting_id not in known_meetings:
            continue
        for participant in meeting:
            if _normalized_name(participant.tag) not in {"participant", "speaker"}:
                continue
            agent = _attribute(
                participant,
                "code",
                "agent",
                "nxt_agent",
                "speaker",
                "channel",
            )
            participant_id = _attribute(
                participant,
                "participant_id",
                "global_name",
                "globalname",
                "name",
            )
            if agent is None or participant_id is None:
                raise ValueError("AMI participant dependency is incomplete")
            key = (meeting_id, agent)
            if key in dependencies and dependencies[key] != participant_id:
                raise ValueError("AMI participant dependency is conflicting")
            dependencies[key] = participant_id
    return dependencies


def _word_boundaries(
    paths: Sequence[Path],
    known_meetings: set[str],
) -> tuple[
    dict[str, tuple[_Boundary, ...]],
    dict[str, dict[str, int]],
]:
    words: dict[str, tuple[_Boundary, ...]] = {}
    identifiers: dict[str, dict[str, int]] = {}
    for path in paths:
        root = _xml(path)
        meeting_id, agent = _source_identity(path, root)
        if meeting_id not in known_meetings:
            raise ValueError(f"AMI annotation references unknown meeting: {meeting_id}")
        ordered: list[_Boundary] = []
        positions: dict[str, int] = {}
        for element in root.iter():
            if _normalized_name(element.tag) not in {"w", "word"}:
                continue
            identifier = _attribute(element, "id")
            if identifier is None or identifier in positions:
                raise ValueError("AMI word identifier is missing or duplicate")
            start_ms = _milliseconds(_attribute(element, "starttime", "start"))
            end_ms = _milliseconds(_attribute(element, "endtime", "end"))
            if not 0 <= start_ms < end_ms:
                raise ValueError("AMI word time span is malformed")
            positions[identifier] = len(ordered)
            ordered.append(_Boundary(meeting_id, agent, start_ms, end_ms))
        if not ordered:
            raise ValueError("AMI word file contains no timing boundaries")
        if path.name in words:
            raise ValueError("duplicate AMI word filename")
        words[path.name] = tuple(ordered)
        identifiers[path.name] = positions
    return words, identifiers


def _timing_boundaries(
    paths: Sequence[Path],
    known_meetings: set[str],
    words: Mapping[str, tuple[_Boundary, ...]],
    word_identifiers: Mapping[str, Mapping[str, int]],
) -> tuple[
    dict[str, tuple[_Boundary, ...]],
    dict[str, dict[str, int]],
]:
    timing: dict[str, tuple[_Boundary, ...]] = {}
    identifiers: dict[str, dict[str, int]] = {}
    for path in paths:
        root = _xml(path)
        meeting_id, agent = _source_identity(path, root)
        if meeting_id not in known_meetings:
            raise ValueError(f"AMI annotation references unknown meeting: {meeting_id}")
        ordered: list[_Boundary] = []
        positions: dict[str, int] = {}
        for element in root.iter():
            if _normalized_name(element.tag) not in {
                "segment",
                "timinglink",
                "turn",
                "utterance",
            }:
                continue
            identifier = _attribute(element, "id")
            if identifier is None or identifier in positions:
                raise ValueError("AMI timing-link identifier is missing or duplicate")
            referenced: list[_Boundary] = []
            for child in element.iter():
                if child is element or _normalized_name(child.tag) not in {
                    "child",
                    "link",
                    "pointer",
                }:
                    continue
                target, first, last = _local_reference(
                    _attribute(child, "href"),
                    path.name,
                )
                referenced.extend(_resolve_range(
                    target,
                    first,
                    last,
                    words,
                    word_identifiers,
                    "word",
                ))
            boundary = _merge_boundaries(referenced)
            if (boundary.meeting_id, boundary.agent) != (meeting_id, agent):
                raise ValueError("AMI timing link crosses source identity")
            positions[identifier] = len(ordered)
            ordered.append(boundary)
        if not ordered:
            raise ValueError("AMI timing-link file contains no local links")
        if path.name in timing:
            raise ValueError("duplicate AMI timing-link filename")
        timing[path.name] = tuple(ordered)
        identifiers[path.name] = positions
    return timing, identifiers


def load_ami_turns(
    metadata_path: Path,
    word_paths: Sequence[Path],
    timing_link_paths: Sequence[Path],
    dialogue_act_paths: Sequence[Path],
    known_meetings: Sequence[str],
) -> tuple[Turn, ...]:
    """Load only local synthetic/verified AMI boundaries; transcript text is discarded."""
    meetings = set(_nonempty_identifiers(known_meetings, "known meetings"))
    dependencies = _metadata_dependencies(Path(metadata_path), meetings)
    word_files = tuple(Path(path) for path in word_paths)
    timing_files = tuple(Path(path) for path in timing_link_paths)
    act_files = tuple(Path(path) for path in dialogue_act_paths)
    if not word_files or not timing_files or not act_files:
        raise ValueError("AMI annotation inputs must be non-empty")
    words, word_identifiers = _word_boundaries(word_files, meetings)
    timing, timing_identifiers = _timing_boundaries(
        timing_files,
        meetings,
        words,
        word_identifiers,
    )
    turns: list[Turn] = []
    for path in act_files:
        root = _xml(path)
        meeting_id, agent = _source_identity(path, root)
        if meeting_id not in meetings:
            raise ValueError(f"AMI annotation references unknown meeting: {meeting_id}")
        participant_id = dependencies.get((meeting_id, agent))
        if participant_id is None:
            raise ValueError(
                f"AMI annotation has unresolved participant: {meeting_id}/{agent}"
            )
        found = False
        for element in root.iter():
            if _normalized_name(element.tag) not in {
                "dact",
                "dialogueact",
                "da",
            }:
                continue
            found = True
            dialogue_act = _attribute(
                element,
                "type",
                "nite_type",
                "dialogue_act",
            )
            if dialogue_act is None:
                raise ValueError("AMI dialogue act is missing")
            referenced: list[_Boundary] = []
            for child in element.iter():
                if child is element or _normalized_name(child.tag) not in {
                    "child",
                    "link",
                    "pointer",
                }:
                    continue
                target, first, last = _local_reference(
                    _attribute(child, "href"),
                    path.name,
                )
                if target in timing:
                    referenced.extend(_resolve_range(
                        target,
                        first,
                        last,
                        timing,
                        timing_identifiers,
                        "timing link",
                    ))
                elif target in words:
                    referenced.extend(_resolve_range(
                        target,
                        first,
                        last,
                        words,
                        word_identifiers,
                        "word",
                    ))
                else:
                    raise ValueError(
                        "AMI NXT reference targets an unknown local annotation file"
                    )
            boundary = _merge_boundaries(referenced)
            if (boundary.meeting_id, boundary.agent) != (meeting_id, agent):
                raise ValueError("AMI dialogue act crosses source identity")
            turns.append(Turn(
                meeting_id=meeting_id,
                participant_id=participant_id,
                start_ms=boundary.start_ms,
                end_ms=boundary.end_ms,
                dialogue_act=dialogue_act.strip().lower(),
            ))
        if not found:
            raise ValueError("AMI dialogue-act file contains no dialogue acts")
    return tuple(sorted(
        turns,
        key=lambda turn: (
            turn.start_ms,
            turn.end_ms,
            turn.participant_id,
        ),
    ))


def _linear_percentile(values: Sequence[int | float], percentile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def _validated_turns(turns: Sequence[Turn]) -> tuple[Turn, ...]:
    if isinstance(turns, (str, bytes)) or not isinstance(turns, Sequence):
        raise ValueError("meeting turns must be a sequence")
    ordered: list[Turn] = []
    for turn in turns:
        if not isinstance(turn, Turn):
            raise ValueError("meeting turns must be Turn records")
        if (
            type(turn.meeting_id) is not str
            or not turn.meeting_id
            or type(turn.participant_id) is not str
            or not turn.participant_id
            or type(turn.dialogue_act) is not str
            or not turn.dialogue_act
        ):
            raise ValueError("meeting turn identifiers are invalid")
        if (
            type(turn.start_ms) is not int
            or type(turn.end_ms) is not int
            or not 0 <= turn.start_ms < turn.end_ms
        ):
            raise ValueError("meeting turn time span is malformed")
        ordered.append(turn)
    if not ordered:
        raise ValueError("meeting requires turns")
    if len({turn.meeting_id for turn in ordered}) != 1:
        raise ValueError("meeting mechanics require turns from one meeting")
    if len({turn.participant_id for turn in ordered}) < 2:
        raise ValueError("meeting mechanics require at least two proven participants")
    return tuple(sorted(
        ordered,
        key=lambda turn: (
            turn.start_ms,
            turn.end_ms,
            turn.participant_id,
        ),
    ))


def _overlap_duration(turns: Sequence[Turn]) -> int:
    events: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for turn in turns:
        events[turn.start_ms].append((turn.participant_id, 1))
        events[turn.end_ms].append((turn.participant_id, -1))
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


def compute_meeting_mechanics(
    turns: Sequence[Turn],
) -> MeetingMechanics:
    ordered = _validated_turns(turns)
    durations = [turn.end_ms - turn.start_ms for turn in ordered]
    nonnegative_gaps = [
        gap
        for current, following in zip(ordered, ordered[1:])
        if (gap := following.start_ms - current.end_ms) >= 0
    ]
    first_start = min(turn.start_ms for turn in ordered)
    last_end = max(turn.end_ms for turn in ordered)
    meeting_span = last_end - first_start
    participants = tuple(sorted({turn.participant_id for turn in ordered}))

    speaking_time: Counter[str] = Counter()
    for turn, duration in zip(ordered, durations):
        speaking_time[turn.participant_id] += duration
    total_speaking_time = sum(speaking_time.values())
    entropy = -sum(
        (duration / total_speaking_time)
        * math.log(duration / total_speaking_time)
        for duration in speaking_time.values()
    )
    normalized_entropy = entropy / math.log(len(participants))

    substantive = [
        turn
        for turn in ordered
        if turn.dialogue_act.strip().lower() != BACKCHANNEL_ACT
    ]
    floor_changes = sum(
        current.participant_id != following.participant_id
        for current, following in zip(substantive, substantive[1:])
    )
    acts = Counter(turn.dialogue_act.strip().lower() for turn in ordered)
    values = (
        ("turn_duration_median_ms", _linear_percentile(durations, 0.5)),
        ("turn_duration_p90_ms", _linear_percentile(durations, 0.9)),
        (
            "inter_turn_gap_median_ms",
            _linear_percentile(nonnegative_gaps, 0.5),
        ),
        (
            "inter_turn_gap_p90_ms",
            _linear_percentile(nonnegative_gaps, 0.9),
        ),
        ("overlap_ratio", _overlap_duration(ordered) / meeting_span),
        (
            "floor_changes_per_minute",
            floor_changes * 60000.0 / meeting_span,
        ),
        ("normalized_speaker_entropy", normalized_entropy),
        (
            "backchannels_per_100_turns",
            acts.get(BACKCHANNEL_ACT, 0) * 100.0 / len(ordered),
        ),
    )
    distribution = tuple(
        (act, count / len(ordered))
        for act, count in sorted(acts.items())
    )
    return MeetingMechanics(
        meeting_id=ordered[0].meeting_id,
        participants=participants,
        values=values,
        dialogue_act_distribution=distribution,
    )


def _validated_meeting(meeting: MeetingMechanics) -> MeetingMechanics:
    if not isinstance(meeting, MeetingMechanics):
        raise ValueError("AMI aggregate inputs must be MeetingMechanics records")
    if type(meeting.meeting_id) is not str or not meeting.meeting_id:
        raise ValueError("AMI meeting identifier is invalid")
    if (
        type(meeting.participants) is not tuple
        or len(meeting.participants) < 2
        or any(type(value) is not str or not value for value in meeting.participants)
        or meeting.participants != tuple(sorted(set(meeting.participants)))
    ):
        raise ValueError("AMI meeting participants are invalid")
    if (
        type(meeting.values) is not tuple
        or tuple(key for key, _ in meeting.values) != VALUE_KEYS
        or any(
            type(value) is not float or not math.isfinite(value)
            for _, value in meeting.values
        )
    ):
        raise ValueError("AMI meeting scalar values are invalid")
    values = dict(meeting.values)
    if any(values[key] < 0.0 for key in BUCKET_VALUE_KEYS):
        raise ValueError("AMI meeting timing bucket is invalid")
    if not 0.0 <= values["overlap_ratio"] <= 1.0:
        raise ValueError("AMI meeting overlap ratio is invalid")
    if values["floor_changes_per_minute"] < 0.0:
        raise ValueError("AMI meeting floor-change rate is invalid")
    if not 0.0 <= values["normalized_speaker_entropy"] <= 1.0:
        raise ValueError("AMI meeting speaker entropy is invalid")
    if not 0.0 <= values["backchannels_per_100_turns"] <= 100.0:
        raise ValueError("AMI meeting backchannel rate is invalid")
    distribution = meeting.dialogue_act_distribution
    if (
        type(distribution) is not tuple
        or not distribution
        or any(
            type(act) is not str
            or not act
            or type(value) is not float
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
            for act, value in distribution
        )
        or tuple(act for act, _ in distribution)
        != tuple(sorted({act for act, _ in distribution}))
        or not math.isclose(
            sum(value for _, value in distribution),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ):
        raise ValueError("AMI meeting dialogue-act distribution is invalid")
    return meeting


def _meeting_digest(meeting: MeetingMechanics) -> str:
    payload = {
        "meeting_id": meeting.meeting_id,
        "participants": meeting.participants,
        "values": meeting.values,
        "dialogue_act_distribution": meeting.dialogue_act_distribution,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _aggregate_cell(
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


def contribution_limited_aggregates(
    meetings: Sequence[MeetingMechanics],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int = 10,
) -> dict[str, Any]:
    if type(minimum_contributors) is not int or minimum_contributors < 10:
        raise ValueError("minimum contributors must be at least 10")
    if isinstance(meetings, (str, bytes)) or not isinstance(meetings, Sequence):
        raise ValueError("AMI meetings must be a sequence")
    validated = tuple(_validated_meeting(meeting) for meeting in meetings)
    by_id = {meeting.meeting_id: meeting for meeting in validated}
    if len(by_id) != len(validated):
        raise ValueError("duplicate meeting identifier")
    if not isinstance(partition_membership, Mapping) or set(
        partition_membership
    ) != set(PARTITION_CELLS):
        raise ValueError("AMI partition membership fields are invalid")
    order = _nonempty_identifiers(official_order, "official meeting order")
    if set(order) != set(by_id):
        raise ValueError("official meeting order does not match meetings")
    order_index = {meeting_id: index for index, meeting_id in enumerate(order)}

    result: dict[str, Any] = {}
    for partition in PARTITION_CELLS:
        member_ids = _nonempty_identifiers(
            partition_membership[partition],
            f"{partition} membership",
        )
        unknown = set(member_ids) - set(by_id)
        if unknown:
            raise ValueError(
                f"AMI partition references unknown meeting: {sorted(unknown)[0]}"
            )
        candidates = sorted(
            (by_id[meeting_id] for meeting_id in member_ids),
            key=lambda meeting: (
                order_index[meeting.meeting_id],
                _meeting_digest(meeting),
            ),
        )
        selected: list[MeetingMechanics] = []
        contributed: set[str] = set()
        repeated = 0
        for meeting in candidates:
            if contributed.intersection(meeting.participants):
                repeated += 1
                continue
            selected.append(meeting)
            contributed.update(meeting.participants)

        participant_count = len(contributed)
        value_maps = [dict(meeting.values) for meeting in selected]
        aggregates = {
            key: sum(values[key] for values in value_maps) / len(value_maps)
            for key in VALUE_KEYS
        }
        dialogue_acts = sorted({
            act
            for meeting in selected
            for act, _ in meeting.dialogue_act_distribution
        })
        distributions = [
            dict(meeting.dialogue_act_distribution)
            for meeting in selected
        ]
        dialogue_aggregates = {
            act: sum(distribution.get(act, 0.0) for distribution in distributions)
            / len(distributions)
            for act in dialogue_acts
        }
        suppressed = participant_count < minimum_contributors
        result[partition] = {
            "meeting_count": len(selected),
            "unique_participant_count": participant_count,
            "scalars": {
                key: _aggregate_cell(
                    aggregates[key],
                    participant_count,
                    minimum_contributors,
                )
                for key in SCALAR_VALUE_KEYS
            },
            "buckets": {
                key: _aggregate_cell(
                    aggregates[key],
                    participant_count,
                    minimum_contributors,
                )
                for key in BUCKET_VALUE_KEYS
            },
            "dialogue_acts": {
                act: _aggregate_cell(
                    value,
                    participant_count,
                    minimum_contributors,
                )
                for act, value in dialogue_aggregates.items()
            },
            "suppression_counts": {
                "repeated_participant_meetings": repeated,
                "scalar_cells": len(SCALAR_VALUE_KEYS) if suppressed else 0,
                "bucket_cells": len(BUCKET_VALUE_KEYS) if suppressed else 0,
                "dialogue_act_cells": len(dialogue_acts) if suppressed else 0,
            },
        }
    return result
