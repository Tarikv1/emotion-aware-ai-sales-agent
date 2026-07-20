from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


PARTITION_CELLS = ("scenario_only", "full_corpus", "full_only")
BUCKET_VALUE_KEYS = (
    "turn_duration_ms_median",
    "turn_duration_ms_p90",
    "inter_turn_gap_ms_median",
    "inter_turn_gap_ms_p90",
)
SCALAR_VALUE_KEYS = (
    "overlap_ratio",
    "floor_changes_per_minute",
    "speaker_balance_normalized_entropy",
    "backchannels_per_100_turns",
)
TIMING_SCALAR_VALUE_KEYS_V2 = (
    "overlap_ratio",
    "speaker_balance_normalized_entropy",
)
VALUE_KEYS = BUCKET_VALUE_KEYS + SCALAR_VALUE_KEYS
BACKCHANNEL_ACT = "ami_da_1"
DIALOGUE_ACT_VOCABULARY = (
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
_DA_ASPECT_TARGET = "da-types.xml"
_SYNTHETIC_LEGACY_SCHEMA = "phase_b_ami_mechanics_v1"
_DA_ASPECT_REFERENCE = re.compile(r"^([^#]+)#id\(([^()]+)\)$")
_REFERENCE_FRAGMENT = re.compile(
    r"^id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?$"
)


@dataclass(frozen=True)
class AmiXmlBytes:
    filename: str
    content: bytes

    def __post_init__(self) -> None:
        if type(self.filename) is not str:
            raise ValueError("AMI filename must be a string")
        normalized = unicodedata.normalize("NFC", self.filename)
        if (
            not normalized
            or normalized != self.filename
            or normalized in {".", ".."}
            or "://" in normalized
            or any(character in normalized for character in ("/", "\\", ":"))
            or any(
                character.isspace()
                or unicodedata.category(character).startswith("C")
                for character in normalized
            )
        ):
            raise ValueError("AMI filename must be a safe local identity")
        if type(self.content) is not bytes:
            raise TypeError("AMI XML content must be bytes")


@dataclass(frozen=True)
class Turn:
    meeting_id: str
    participant_id: str
    start_ms: int
    end_ms: int
    dialogue_act: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "meeting_id",
            _canonical_identifier(self.meeting_id, "meeting"),
        )
        object.__setattr__(
            self,
            "participant_id",
            _canonical_identifier(self.participant_id, "participant"),
        )
        object.__setattr__(
            self,
            "dialogue_act",
            _canonical_dialogue_act(self.dialogue_act),
        )


@dataclass(frozen=True)
class TimedTurn:
    meeting_id: str
    participant_id: str
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        if (
            type(self.meeting_id) is not str
            or self.meeting_id
            != _canonical_identifier(self.meeting_id, "meeting")
        ):
            raise ValueError("timed-turn meeting identifier is invalid")
        if (
            type(self.participant_id) is not str
            or self.participant_id
            != _canonical_identifier(self.participant_id, "participant")
        ):
            raise ValueError("timed-turn participant identifier is invalid")
        if (
            type(self.start_ms) is not int
            or type(self.end_ms) is not int
            or not 0 <= self.start_ms < self.end_ms
        ):
            raise ValueError("timed-turn span is malformed")


@dataclass(frozen=True)
class AmiMeetingEvidenceV2:
    meeting_id: str
    participants: tuple[str, ...]
    timing_file_present: bool
    timed_turns: tuple[TimedTurn, ...] | None
    dialogue_turns: tuple[Turn, ...] | None
    dialogue_act_file_count: int
    fully_labeled_dialogue_act_file_count: int
    unlabeled_dialogue_act_record_count: int
    unlabeled_dialogue_act_file_count: int

    def __post_init__(self) -> None:
        _validated_ami_meeting_evidence_v2(self)


@dataclass(frozen=True)
class MeetingMechanics:
    meeting_id: str
    participants: tuple[str, ...]
    values: tuple[tuple[str, float], ...]
    dialogue_act_distribution: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "meeting_id",
            _canonical_identifier(self.meeting_id, "meeting"),
        )
        if type(self.participants) is not tuple:
            raise ValueError("participant identifiers must be a tuple")
        canonical = tuple(sorted({
            _canonical_identifier(participant, "participant")
            for participant in self.participants
        }))
        object.__setattr__(self, "participants", canonical)
        if type(self.dialogue_act_distribution) is not tuple:
            raise ValueError("dialogue-act distribution must be a tuple")
        distribution = tuple(sorted(
            (
                _canonical_dialogue_act(dialogue_act),
                value,
            )
            for dialogue_act, value in self.dialogue_act_distribution
        ))
        if len({label for label, _ in distribution}) != len(distribution):
            raise ValueError("dialogue-act vocabulary contains an alias")
        object.__setattr__(
            self,
            "dialogue_act_distribution",
            distribution,
        )


@dataclass(frozen=True)
class _Boundary:
    meeting_id: str
    agent: str
    start_ms: int
    end_ms: int


def _canonical_identifier(value: Any, name: str) -> str:
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


def _canonical_dialogue_act(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("dialogue-act vocabulary label must be a string")
    canonical = unicodedata.normalize("NFC", value.strip().lower())
    if canonical not in DIALOGUE_ACT_VOCABULARY:
        raise ValueError("dialogue-act vocabulary label is not allowed")
    return canonical


def _normalized_name(name: str) -> str:
    local_name = name.rsplit("}", 1)[-1].split(":")[-1].lower()
    return re.sub(r"[^a-z0-9]", "", local_name)


def _exact_local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _exact_attribute(element: ET.Element, name: str) -> str | None:
    values = [
        value
        for key, value in element.attrib.items()
        if _exact_local_name(key) == name and value.strip()
    ]
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("conflicting exact XML attributes")
    return values[0]


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


def _xml(source: AmiXmlBytes) -> ET.Element:
    try:
        return ET.fromstring(source.content)
    except ET.ParseError as error:
        raise ValueError(
            f"AMI XML is unreadable: {source.filename}"
        ) from error


def _nonempty_identifiers(
    values: Sequence[str],
    name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    normalized = tuple(
        _canonical_identifier(value, name.rstrip("s"))
        for value in values
    )
    if (
        not normalized
        or len(set(normalized)) != len(normalized)
    ):
        raise ValueError(f"{name} must contain unique canonical identifiers")
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


def _source_identity(source: AmiXmlBytes, root: ET.Element) -> tuple[str, str]:
    meeting_id = _attribute(root, "meeting_id", "meeting", "observation")
    agent = _attribute(root, "agent", "speaker", "participant", "channel")
    parts = source.filename.split(".")
    if meeting_id is None and len(parts) >= 3:
        meeting_id = parts[0]
    if agent is None and len(parts) >= 3:
        agent = parts[1]
    if meeting_id is None or agent is None:
        raise ValueError("AMI annotation source identity is incomplete")
    return (
        _canonical_identifier(meeting_id, "meeting"),
        _canonical_identifier(agent, "speaker dependency"),
    )


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


def _dialogue_act_from_element(
    element: ET.Element,
    *,
    allow_legacy_direct: bool,
) -> str | None:
    direct_values = [
        value
        for name in ("type", "niteType", "nite_type", "dialogue_act")
        if (value := _exact_attribute(element, name)) is not None
    ]
    if len(direct_values) > 1:
        raise ValueError("AMI dialogue act has conflicting direct labels")
    direct = direct_values[0] if direct_values else None
    aspect_pointers = [
        child
        for child in element.iter()
        if (
            child is not element
            and _exact_local_name(child.tag) == "pointer"
            and _exact_attribute(child, "role") == "da-aspect"
        )
    ]
    if direct is not None:
        if not allow_legacy_direct:
            raise ValueError(
                "AMI real-schema dialogue act requires a da-aspect pointer"
            )
        if aspect_pointers:
            raise ValueError(
                "AMI dialogue act cannot mix a direct label and da-aspect pointer"
            )
        if direct not in DIALOGUE_ACT_VOCABULARY:
            raise ValueError("dialogue-act vocabulary label is not allowed")
        return direct
    if not aspect_pointers:
        return None
    if len(aspect_pointers) != 1:
        raise ValueError(
            "AMI dialogue act must have exactly one da-aspect pointer"
        )
    href = _exact_attribute(aspect_pointers[0], "href")
    if href is None:
        raise ValueError("AMI da-aspect pointer is malformed")
    if (
        "://" in href
        or href.startswith(("/", "\\"))
        or "\\" in href
        or "/" in href
        or ":" in href
    ):
        raise ValueError("AMI NXT reference uses an external URI")
    match = _DA_ASPECT_REFERENCE.fullmatch(href)
    if match is None:
        raise ValueError("AMI da-aspect pointer is malformed")
    target, label = match.groups()
    if target != _DA_ASPECT_TARGET:
        if target.strip().casefold() == _DA_ASPECT_TARGET.casefold():
            raise ValueError("AMI da-aspect pointer is malformed")
        raise ValueError("AMI da-aspect target is not the official local ontology")
    if label not in DIALOGUE_ACT_VOCABULARY:
        if label.strip().casefold() in DIALOGUE_ACT_VOCABULARY:
            raise ValueError("AMI da-aspect pointer is malformed")
        raise ValueError("dialogue-act vocabulary label is not allowed")
    return label


def _metadata_dependencies(
    metadata: AmiXmlBytes,
    known_meetings: set[str],
    participant_metadata: AmiXmlBytes | None = None,
) -> dict[tuple[str, str], str]:
    dependencies: dict[tuple[str, str], str] = {}
    for meeting in _xml(metadata).iter():
        if _exact_local_name(meeting.tag) != "meeting":
            continue
        observation = _exact_attribute(meeting, "observation")
        real_schema = observation is not None
        meeting_id = (
            observation
            if real_schema
            else _exact_attribute(meeting, "id")
        )
        if meeting_id is None:
            continue
        meeting_id = _canonical_identifier(meeting_id, "meeting")
        if meeting_id not in known_meetings:
            continue
        for participant in meeting:
            local_name = _exact_local_name(participant.tag)
            if real_schema:
                if local_name != "speaker":
                    if _normalized_name(participant.tag) in {
                        "participant",
                        "speaker",
                    }:
                        raise ValueError(
                            "AMI participant dependency is incomplete"
                        )
                    continue
                agent = _exact_attribute(participant, "nxt_agent")
                participant_id = _exact_attribute(
                    participant,
                    "global_name",
                )
            else:
                if local_name != "participant":
                    if _normalized_name(participant.tag) in {
                        "participant",
                        "speaker",
                    }:
                        raise ValueError(
                            "AMI participant dependency is incomplete"
                        )
                    continue
                agent = _exact_attribute(participant, "code")
                participant_id = _exact_attribute(
                    participant,
                    "participant_id",
                )
            if agent is None or participant_id is None:
                raise ValueError("AMI participant dependency is incomplete")
            agent = _canonical_identifier(agent, "speaker dependency")
            participant_id = _canonical_identifier(
                participant_id,
                "participant",
            )
            key = (meeting_id, agent)
            if key in dependencies:
                raise ValueError("AMI participant dependency is conflicting")
            dependencies[key] = participant_id
    if participant_metadata is not None:
        enriched: set[str] = set()
        for participant in _xml(participant_metadata).iter():
            local_name = _exact_local_name(participant.tag)
            if local_name != "participant":
                if _normalized_name(participant.tag) == "participant":
                    raise ValueError("AMI participant enrichment is incomplete")
                continue
            participant_id = _exact_attribute(participant, "id")
            if participant_id is None:
                raise ValueError("AMI participant enrichment is incomplete")
            participant_id = _canonical_identifier(
                participant_id,
                "participant",
            )
            if participant_id in enriched:
                raise ValueError("AMI participant enrichment is conflicting")
            enriched.add(participant_id)
        if not enriched:
            raise ValueError("AMI participant enrichment is incomplete")
    return dependencies


def _word_boundaries(
    sources: Sequence[AmiXmlBytes],
    known_meetings: set[str],
) -> tuple[
    dict[str, tuple[_Boundary, ...]],
    dict[str, dict[str, int]],
]:
    words: dict[str, tuple[_Boundary, ...]] = {}
    identifiers: dict[str, dict[str, int]] = {}
    for source in sources:
        root = _xml(source)
        meeting_id, agent = _source_identity(source, root)
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
        if source.filename in words:
            raise ValueError("duplicate AMI word filename")
        words[source.filename] = tuple(ordered)
        identifiers[source.filename] = positions
    return words, identifiers


def _timing_boundaries(
    sources: Sequence[AmiXmlBytes],
    known_meetings: set[str],
    words: Mapping[str, tuple[_Boundary, ...]],
    word_identifiers: Mapping[str, Mapping[str, int]],
) -> tuple[
    dict[str, tuple[_Boundary, ...]],
    dict[str, dict[str, int]],
]:
    timing: dict[str, tuple[_Boundary, ...]] = {}
    identifiers: dict[str, dict[str, int]] = {}
    for source in sources:
        root = _xml(source)
        meeting_id, agent = _source_identity(source, root)
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
                    source.filename,
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
        if source.filename in timing:
            raise ValueError("duplicate AMI timing-link filename")
        timing[source.filename] = tuple(ordered)
        identifiers[source.filename] = positions
    return timing, identifiers


def load_ami_turns(
    metadata_path: Path,
    word_paths: Sequence[Path],
    timing_link_paths: Sequence[Path],
    dialogue_act_paths: Sequence[Path],
    known_meetings: Sequence[str],
    *,
    participant_metadata_path: Path | None = None,
    expected_unlabeled_count: int = 0,
) -> tuple[Turn, ...]:
    return load_ami_turns_from_bytes(
        _ami_xml_bytes_from_path(metadata_path),
        tuple(_ami_xml_bytes_from_path(path) for path in word_paths),
        tuple(_ami_xml_bytes_from_path(path) for path in timing_link_paths),
        tuple(_ami_xml_bytes_from_path(path) for path in dialogue_act_paths),
        known_meetings,
        participant_metadata=(
            None
            if participant_metadata_path is None
            else _ami_xml_bytes_from_path(participant_metadata_path)
        ),
        expected_unlabeled_count=expected_unlabeled_count,
    )


def _ami_xml_bytes_from_path(path: Path) -> AmiXmlBytes:
    source = Path(path)
    try:
        content = source.read_bytes()
    except OSError as error:
        raise ValueError(f"AMI XML is unreadable: {source.name}") from error
    return AmiXmlBytes(source.name, content)


def _validated_ami_sources(
    sources: Sequence[AmiXmlBytes],
    name: str,
) -> tuple[AmiXmlBytes, ...]:
    if isinstance(sources, (str, bytes)) or not isinstance(sources, Sequence):
        raise ValueError(f"{name} must be a sequence of AMI XML bytes")
    validated = tuple(sources)
    if not validated:
        raise ValueError("AMI annotation inputs must be non-empty")
    if any(type(source) is not AmiXmlBytes for source in validated):
        raise ValueError(f"{name} must contain only AMI XML bytes")
    return validated


def load_ami_turns_from_bytes(
    metadata: AmiXmlBytes,
    word_sources: Sequence[AmiXmlBytes],
    timing_link_sources: Sequence[AmiXmlBytes],
    dialogue_act_sources: Sequence[AmiXmlBytes],
    known_meetings: Sequence[str],
    *,
    participant_metadata: AmiXmlBytes | None = None,
    expected_unlabeled_count: int = 0,
) -> tuple[Turn, ...]:
    """Load local AMI identities from verified bytes; transcript text is discarded."""
    if type(expected_unlabeled_count) is not int or expected_unlabeled_count < 0:
        raise ValueError(
            "AMI expected unlabeled count must be a non-negative integer"
        )
    if type(metadata) is not AmiXmlBytes:
        raise ValueError("metadata must be AMI XML bytes")
    if (
        participant_metadata is not None
        and type(participant_metadata) is not AmiXmlBytes
    ):
        raise ValueError("participant metadata must be AMI XML bytes")
    word_files = _validated_ami_sources(word_sources, "word sources")
    timing_files = _validated_ami_sources(
        timing_link_sources,
        "timing-link sources",
    )
    act_files = _validated_ami_sources(
        dialogue_act_sources,
        "dialogue-act sources",
    )
    all_sources = (
        (metadata,)
        + word_files
        + timing_files
        + act_files
        + (() if participant_metadata is None else (participant_metadata,))
    )
    filenames = tuple(source.filename for source in all_sources)
    if len(filenames) != len(set(filenames)):
        raise ValueError("duplicate AMI filename")

    meetings = set(_nonempty_identifiers(known_meetings, "known meetings"))
    dependencies = _metadata_dependencies(
        metadata,
        meetings,
        participant_metadata,
    )
    words, word_identifiers = _word_boundaries(word_files, meetings)
    timing, timing_identifiers = _timing_boundaries(
        timing_files,
        meetings,
        words,
        word_identifiers,
    )
    turns: list[Turn] = []
    unlabeled_count = 0
    for source in act_files:
        root = _xml(source)
        legacy_schema = _exact_attribute(root, "synthetic_legacy_schema")
        if (
            legacy_schema is not None
            and legacy_schema != _SYNTHETIC_LEGACY_SCHEMA
        ):
            raise ValueError("AMI synthetic legacy schema marker is invalid")
        allow_legacy_direct = legacy_schema == _SYNTHETIC_LEGACY_SCHEMA
        meeting_id, agent = _source_identity(source, root)
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
            dialogue_act = _dialogue_act_from_element(
                element,
                allow_legacy_direct=allow_legacy_direct,
            )
            referenced: list[_Boundary] = []
            for child in element.iter():
                if child is element or _normalized_name(child.tag) not in {
                    "child",
                    "link",
                    "pointer",
                }:
                    continue
                if (
                    _exact_local_name(child.tag) == "pointer"
                    and _exact_attribute(child, "role") == "da-aspect"
                ):
                    continue
                target, first, last = _local_reference(
                    _attribute(child, "href"),
                    source.filename,
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
            if dialogue_act is None:
                unlabeled_count += 1
                continue
            turns.append(Turn(
                meeting_id=meeting_id,
                participant_id=participant_id,
                start_ms=boundary.start_ms,
                end_ms=boundary.end_ms,
                dialogue_act=dialogue_act,
            ))
        if not found:
            raise ValueError("AMI dialogue-act file contains no dialogue acts")
    if unlabeled_count != expected_unlabeled_count:
        raise ValueError("AMI dialogue-act unlabeled count does not match expected")
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
            turn.meeting_id
            != _canonical_identifier(turn.meeting_id, "meeting")
            or turn.participant_id
            != _canonical_identifier(turn.participant_id, "participant")
            or turn.dialogue_act != _canonical_dialogue_act(turn.dialogue_act)
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
        ("turn_duration_ms_median", _linear_percentile(durations, 0.5)),
        ("turn_duration_ms_p90", _linear_percentile(durations, 0.9)),
        (
            "inter_turn_gap_ms_median",
            _linear_percentile(nonnegative_gaps, 0.5),
        ),
        (
            "inter_turn_gap_ms_p90",
            _linear_percentile(nonnegative_gaps, 0.9),
        ),
        ("overlap_ratio", _overlap_duration(ordered) / meeting_span),
        (
            "floor_changes_per_minute",
            floor_changes * 60000.0 / meeting_span,
        ),
        ("speaker_balance_normalized_entropy", normalized_entropy),
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
    if (
        meeting.meeting_id
        != _canonical_identifier(meeting.meeting_id, "meeting")
    ):
        raise ValueError("AMI meeting identifier is invalid")
    if (
        type(meeting.participants) is not tuple
        or len(meeting.participants) < 2
        or any(
            value != _canonical_identifier(value, "participant")
            for value in meeting.participants
        )
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
    if not 0.0 <= values["speaker_balance_normalized_entropy"] <= 1.0:
        raise ValueError("AMI meeting speaker entropy is invalid")
    if not 0.0 <= values["backchannels_per_100_turns"] <= 100.0:
        raise ValueError("AMI meeting backchannel rate is invalid")
    distribution = meeting.dialogue_act_distribution
    if (
        type(distribution) is not tuple
        or not distribution
        or any(
            type(act) is not str
            or act != _canonical_dialogue_act(act)
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


def _strict_identifier_sequence_v2(
    values: Sequence[str],
    name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    identifiers = tuple(values)
    if not identifiers:
        raise ValueError(f"{name} must be non-empty")
    for value in identifiers:
        if (
            type(value) is not str
            or value != _canonical_identifier(value, name.rstrip("s"))
        ):
            raise ValueError(f"{name} must contain canonical identifiers")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{name} must contain unique identifiers")
    return identifiers


def _validated_ami_meeting_evidence_v2(
    evidence: AmiMeetingEvidenceV2,
) -> AmiMeetingEvidenceV2:
    if type(evidence) is not AmiMeetingEvidenceV2:
        raise ValueError(
            "AMI v2 aggregate inputs must be AmiMeetingEvidenceV2 records"
        )
    if (
        type(evidence.meeting_id) is not str
        or evidence.meeting_id
        != _canonical_identifier(evidence.meeting_id, "meeting")
    ):
        raise ValueError("AMI v2 meeting identifier is invalid")
    if type(evidence.participants) is not tuple:
        raise ValueError("AMI v2 participants must be a tuple")
    participants = evidence.participants
    if len(participants) < 2:
        raise ValueError(
            "AMI v2 meeting requires at least two authoritative participants"
        )
    for participant in participants:
        if (
            type(participant) is not str
            or participant
            != _canonical_identifier(participant, "participant")
        ):
            raise ValueError("AMI v2 participant identifier is invalid")
    if participants != tuple(sorted(set(participants))):
        raise ValueError(
            "AMI v2 participants must be unique and canonically ordered"
        )
    if type(evidence.timing_file_present) is not bool:
        raise ValueError("AMI v2 timing-file presence must be a boolean")

    timed_turns = evidence.timed_turns
    if timed_turns is not None:
        if type(timed_turns) is not tuple or not timed_turns:
            raise ValueError(
                "AMI v2 timed turns must be a non-empty tuple or null"
            )
        if any(type(turn) is not TimedTurn for turn in timed_turns):
            raise ValueError(
                "AMI v2 timed turns must contain only TimedTurn records"
            )
        if any(turn.meeting_id != evidence.meeting_id for turn in timed_turns):
            raise ValueError("AMI v2 timed turn crosses meeting identity")
        if any(
            turn.participant_id not in participants
            for turn in timed_turns
        ):
            raise ValueError(
                "AMI v2 timed turn references an unknown participant"
            )
        timed_key = lambda turn: (
            turn.start_ms,
            turn.end_ms,
            turn.participant_id,
        )
        if timed_turns != tuple(sorted(timed_turns, key=timed_key)):
            raise ValueError("AMI v2 timed-turn order is ambiguous")
        if len(set(timed_turns)) != len(timed_turns):
            raise ValueError("AMI v2 timed turns contain an exact duplicate")
        if len({turn.participant_id for turn in timed_turns}) < 2:
            raise ValueError(
                "AMI v2 usable timing requires two represented participants"
            )
    if timed_turns is not None and not evidence.timing_file_present:
        raise ValueError(
            "AMI v2 timed turns require a present timing source file"
        )

    dialogue_turns = evidence.dialogue_turns
    if dialogue_turns is not None:
        if type(dialogue_turns) is not tuple or not dialogue_turns:
            raise ValueError(
                "AMI v2 dialogue turns must be a non-empty tuple or null"
            )
        if any(type(turn) is not Turn for turn in dialogue_turns):
            raise ValueError(
                "AMI v2 dialogue turns must contain only Turn records"
            )
        if any(
            turn.meeting_id != evidence.meeting_id
            for turn in dialogue_turns
        ):
            raise ValueError("AMI v2 dialogue turn crosses meeting identity")
        if any(
            turn.participant_id not in participants
            for turn in dialogue_turns
        ):
            raise ValueError(
                "AMI v2 dialogue turn references an unknown participant"
            )
        for turn in dialogue_turns:
            if (
                turn.meeting_id
                != _canonical_identifier(turn.meeting_id, "meeting")
                or turn.participant_id
                != _canonical_identifier(turn.participant_id, "participant")
                or turn.dialogue_act
                != _canonical_dialogue_act(turn.dialogue_act)
                or type(turn.start_ms) is not int
                or type(turn.end_ms) is not int
                or not 0 <= turn.start_ms < turn.end_ms
            ):
                raise ValueError("AMI v2 dialogue turn is malformed")
        dialogue_key = lambda turn: (
            turn.start_ms,
            turn.end_ms,
            turn.participant_id,
            turn.dialogue_act,
        )
        if dialogue_turns != tuple(sorted(dialogue_turns, key=dialogue_key)):
            raise ValueError("AMI v2 dialogue-turn order is ambiguous")
        if len(set(dialogue_turns)) != len(dialogue_turns):
            raise ValueError(
                "AMI v2 dialogue turns contain an exact duplicate"
            )

    count_names = (
        "dialogue_act_file_count",
        "fully_labeled_dialogue_act_file_count",
        "unlabeled_dialogue_act_record_count",
        "unlabeled_dialogue_act_file_count",
    )
    for name in count_names:
        value = getattr(evidence, name)
        if type(value) is not int or value < 0:
            raise ValueError(
                f"AMI v2 {name} must be a non-negative integer"
            )
    file_count = evidence.dialogue_act_file_count
    fully_labeled_count = evidence.fully_labeled_dialogue_act_file_count
    unlabeled_record_count = evidence.unlabeled_dialogue_act_record_count
    unlabeled_file_count = evidence.unlabeled_dialogue_act_file_count
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
            "AMI v2 unlabeled records cannot be fewer than unlabeled files"
        )
    incomplete_file_count = file_count - fully_labeled_count
    if unlabeled_file_count != incomplete_file_count:
        raise ValueError(
            "AMI v2 incomplete dialogue files require unlabeled records"
        )
    if incomplete_file_count == 0 and unlabeled_record_count != 0:
        raise ValueError(
            "AMI v2 unlabeled counts require an incomplete dialogue file"
        )
    if dialogue_turns is not None and (
        file_count == 0 or incomplete_file_count != 0
    ):
        raise ValueError(
            "AMI v2 dialogue turns cannot assert incomplete evidence complete"
        )
    return evidence


def _timing_values_v2(
    timed_turns: tuple[TimedTurn, ...],
) -> dict[str, float]:
    durations = [
        turn.end_ms - turn.start_ms
        for turn in timed_turns
    ]
    nonnegative_gaps = [
        gap
        for current, following in zip(timed_turns, timed_turns[1:])
        if (gap := following.start_ms - current.end_ms) >= 0
    ]
    meeting_span = (
        max(turn.end_ms for turn in timed_turns)
        - min(turn.start_ms for turn in timed_turns)
    )
    speaking_time: Counter[str] = Counter()
    for turn, duration in zip(timed_turns, durations):
        speaking_time[turn.participant_id] += duration
    total_speaking_time = sum(speaking_time.values())
    entropy = -sum(
        (duration / total_speaking_time)
        * math.log(duration / total_speaking_time)
        for duration in speaking_time.values()
    )
    normalized_entropy = entropy / math.log(len(speaking_time))
    try:
        values = {
            "turn_duration_ms_median": _linear_percentile(
                durations,
                0.5,
            ),
            "turn_duration_ms_p90": _linear_percentile(
                durations,
                0.9,
            ),
            "inter_turn_gap_ms_median": _linear_percentile(
                nonnegative_gaps,
                0.5,
            ),
            "inter_turn_gap_ms_p90": _linear_percentile(
                nonnegative_gaps,
                0.9,
            ),
            "overlap_ratio": (
                _overlap_duration(timed_turns) / meeting_span
            ),
            "speaker_balance_normalized_entropy": normalized_entropy,
        }
    except OverflowError as error:
        raise ValueError(
            "AMI v2 per-meeting timing values must be finite"
        ) from error
    if any(not math.isfinite(value) for value in values.values()):
        raise ValueError(
            "AMI v2 per-meeting timing values must be finite"
        )
    return values


def _select_contributors_v2(
    meetings: tuple[AmiMeetingEvidenceV2, ...],
) -> tuple[
    tuple[AmiMeetingEvidenceV2, ...],
    int,
    set[str],
]:
    selected: list[AmiMeetingEvidenceV2] = []
    contributed: set[str] = set()
    repeated = 0
    for meeting in meetings:
        if contributed.intersection(meeting.participants):
            repeated += 1
            continue
        selected.append(meeting)
        contributed.update(meeting.participants)
    return tuple(selected), repeated, contributed


def _timing_family_v2(
    candidates: tuple[AmiMeetingEvidenceV2, ...],
    minimum_contributors: int,
) -> dict[str, Any]:
    coverage = {
        "timing_file_meeting_count": sum(
            meeting.timing_file_present
            for meeting in candidates
        ),
        "usable_timing_meeting_count": sum(
            meeting.timed_turns is not None
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

    selected, repeated, contributed = _select_contributors_v2(candidates)
    if len(selected) + repeated != len(candidates):
        raise ValueError("AMI v2 timing contribution accounting is invalid")
    participant_count = len(contributed)
    value_maps = [
        _timing_values_v2(meeting.timed_turns)
        for meeting in selected
        if meeting.timed_turns is not None
    ]
    aggregates = {
        key: sum(values[key] for values in value_maps) / len(value_maps)
        for key in BUCKET_VALUE_KEYS + TIMING_SCALAR_VALUE_KEYS_V2
    }
    if any(not math.isfinite(value) for value in aggregates.values()):
        raise ValueError("AMI v2 aggregate timing values must be finite")
    suppressed = participant_count < minimum_contributors
    contribution = {
        "selected_meeting_count": len(selected),
        "unique_participant_count": participant_count,
        "repeated_participant_meeting_count": repeated,
        "suppressed": suppressed,
    }
    return {
        "status": "available",
        "reason_codes": [],
        "coverage": coverage,
        "contribution": contribution,
        "buckets": {
            key: _aggregate_cell(
                aggregates[key],
                participant_count,
                minimum_contributors,
            )
            for key in BUCKET_VALUE_KEYS
        },
        "scalars": {
            key: _aggregate_cell(
                aggregates[key],
                participant_count,
                minimum_contributors,
            )
            for key in TIMING_SCALAR_VALUE_KEYS_V2
        },
    }


def _dialogue_act_family_v2(
    candidates: tuple[AmiMeetingEvidenceV2, ...],
) -> dict[str, Any]:
    coverage = {
        "dialogue_act_meeting_count": sum(
            meeting.dialogue_act_file_count > 0
            for meeting in candidates
        ),
        "dialogue_act_file_count": sum(
            meeting.dialogue_act_file_count
            for meeting in candidates
        ),
        "fully_labeled_dialogue_act_file_count": sum(
            meeting.fully_labeled_dialogue_act_file_count
            for meeting in candidates
        ),
    }
    reason_codes: list[str] = []
    if coverage["dialogue_act_meeting_count"] != len(candidates):
        reason_codes.append(
            "incomplete_dialogue_act_meeting_coverage"
        )
    if any(
        meeting.unlabeled_dialogue_act_record_count > 0
        or meeting.unlabeled_dialogue_act_file_count > 0
        or meeting.fully_labeled_dialogue_act_file_count
        != meeting.dialogue_act_file_count
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


def contribution_limited_aggregates_v2(
    meetings: Sequence[AmiMeetingEvidenceV2],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int = 10,
) -> dict[str, Any]:
    if (
        type(minimum_contributors) is not int
        or minimum_contributors < 10
    ):
        raise ValueError("minimum contributors must be at least 10")
    if isinstance(meetings, (str, bytes)) or not isinstance(
        meetings,
        Sequence,
    ):
        raise ValueError("AMI v2 meetings must be a sequence")
    validated = tuple(
        _validated_ami_meeting_evidence_v2(meeting)
        for meeting in meetings
    )
    by_id = {
        meeting.meeting_id: meeting
        for meeting in validated
    }
    if len(by_id) != len(validated):
        raise ValueError("duplicate AMI v2 meeting identifier")
    if not isinstance(partition_membership, Mapping) or set(
        partition_membership
    ) != set(PARTITION_CELLS):
        raise ValueError("AMI v2 partition membership fields are invalid")
    membership = {
        partition: _strict_identifier_sequence_v2(
            partition_membership[partition],
            f"{partition} memberships",
        )
        for partition in PARTITION_CELLS
    }
    scenario = set(membership["scenario_only"])
    full_only = set(membership["full_only"])
    full_corpus = set(membership["full_corpus"])
    if not scenario.isdisjoint(full_only):
        raise ValueError(
            "AMI v2 scenario-only and full-only partitions must be disjoint"
        )
    if scenario | full_only != full_corpus:
        raise ValueError(
            "AMI v2 partition union must equal the full corpus"
        )
    order = _strict_identifier_sequence_v2(
        official_order,
        "official meeting orders",
    )
    if set(order) != full_corpus:
        raise ValueError(
            "AMI v2 official order must contain exactly the full corpus"
        )
    if set(by_id) != full_corpus:
        raise ValueError(
            "AMI v2 evidence must contain exactly the full corpus"
        )

    member_sets = {
        partition: set(member_ids)
        for partition, member_ids in membership.items()
    }
    partitions: dict[str, Any] = {}
    for partition in PARTITION_CELLS:
        candidates = tuple(
            by_id[meeting_id]
            for meeting_id in order
            if meeting_id in member_sets[partition]
        )
        partitions[partition] = {
            "population_meeting_count": len(candidates),
            "metric_families": {
                "timing": _timing_family_v2(
                    candidates,
                    minimum_contributors,
                ),
                "dialogue_act": _dialogue_act_family_v2(candidates),
            },
        }
    return {
        "schema_id": "emotion-state-ami-mechanics-aggregate-v2",
        "schema_version": 2,
        "source_quality": {
            "unlabeled_dialogue_act_record_count": sum(
                meeting.unlabeled_dialogue_act_record_count
                for meeting in validated
            ),
            "unlabeled_dialogue_act_file_count": sum(
                meeting.unlabeled_dialogue_act_file_count
                for meeting in validated
            ),
        },
        "partitions": partitions,
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
