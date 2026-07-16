from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import unicodedata
import wave
import zipfile
from collections.abc import Mapping
from copy import deepcopy
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any
from xml.etree import ElementTree

CREMA_DATASET_ID = "crema-d-v1.0-audio-wav"
AMI_DATASET_ID = "ami-manual-annotations-v1.6.2"
SELECTED_PUBLIC_DATASETS = (CREMA_DATASET_ID, AMI_DATASET_ID)

OPERATIONAL_SIGNALS = frozenset({
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
})
REQUIRED_V1_FIELDS = frozenset({
    "dataset_id",
    "canonical_source_url",
    "release_or_version",
    "accessed_on",
    "terms_or_license",
    "access_restrictions",
    "local_file_hashes",
    "source_label",
    "source_labels",
    "project_label_mapping",
    "excluded_labels",
    "language",
    "domain",
    "domain_limitations",
    "permitted_research_lanes",
    "redistribution_status",
})
REQUIRED_V2_FIELDS = REQUIRED_V1_FIELDS | frozenset({
    "manifest_version",
    "selected_artifacts",
    "source_revision",
    "release_published_at",
    "dependency_keys",
    "quality_rules",
    "known_issues",
    "exclusion_inventory",
    "hash_inventory",
    "completion_status",
    "runtime_influence_allowed",
})

CREMA_RAW_SOURCE_LABEL_MAP = {
    "A": "anger",
    "D": "disgust",
    "F": "fear",
    "H": "happy",
    "N": "neutral",
    "S": "sad",
}
CREMA_PROHIBITED_PROJECT_MAPPINGS = {
    "anger": "frustration",
    "happy": "interest",
    "sad": "disengagement",
    "fear": "hesitation",
    "neutral": "no_customer_concern",
}

CREMA_PROFILE_IDENTITY = {
    "canonical_source_url": "https://github.com/CheyneyComputerScience/CREMA-D",
    "release_or_version": "v1.0",
    "source_revision": "f3b8611a309886568dfa957141775b2e05add04a",
    "release_published_at": "2025-03-18T09:54:26Z",
    "terms_or_license": ["ODbL-1.0", "DbCL-1.0"],
    "language": "English",
    "domain": "acted isolated utterances with controlled sentences",
    "selected_artifacts": [
        "AudioWAV/",
        "processedResults/summaryTable.csv",
        "finishedResponses.csv#audio-only-rows",
        "SentenceFilenames.csv",
        "README.md",
        "LICENSE.txt",
        "git-lfs-pointer-metadata",
    ],
}
AMI_PROFILE_IDENTITY = {
    "canonical_source_url": "https://groups.inf.ed.ac.uk/ami/download/",
    "release_or_version": "AMI manual annotations v1.6.2",
    "release_published_at": "2017-04-10",
    "terms_or_license": ["CC-BY-4.0"],
    "language": "English",
    "domain": "scenario-based and naturally occurring multi-party meetings",
    "selected_artifacts": [
        "official-manual-annotation-archive",
        "nxt-metadata",
        "speaker-aligned-orthographic-transcripts",
        "timing-links",
        "dialogue-acts",
        "official-partition-metadata",
        "official-release-license-page-provenance",
    ],
}

DEPENDENCY_KEYS = [
    "speaker",
    "call_session",
    "dialogue_dyad",
    "source_corpus",
    "scripted_scenario",
    "meeting_series",
    "recording_site",
]
PROJECT_OPERATIONAL_SIGNAL_ORDER = [
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
]

CREMA_PROFILE_SELECTION = {
    "source_label": "public-only",
    "source_labels": ["anger", "disgust", "fear", "happy", "neutral", "sad"],
    "project_label_mapping": {},
    "excluded_labels": PROJECT_OPERATIONAL_SIGNAL_ORDER,
    "access_restrictions": [
        "separate_download_authorization_required",
        "official_access_process_required",
        "git_lfs_media_objects_required",
        "ordinary_github_zip_lfs_pointer_stubs_are_not_accepted",
    ],
    "domain_limitations": [
        "acted_speech_is_not_customer_emotion_truth",
        "isolated_controlled_utterances_do_not_validate_sales_calls_or_natural_conversation",
        "audio_only_crowd_perception_labels_do_not_map_to_project_operational_signals",
        "raters_heard_audio_presentation_files_while_feature_checks_use_corresponding_wav_files",
        "recording_site_identity_is_unavailable_and_site_generalization_is_blocked",
    ],
    "permitted_research_lanes": [
        "controlled acoustic feature sensitivity",
        "fixed-sentence lexical negative controls",
        "speaker-disjoint acted-speech diagnostics",
        "offline thesis limitations analysis",
    ],
    "redistribution_status": "not_permitted_from_this_project",
    "dependency_keys": DEPENDENCY_KEYS,
    "quality_rules": [
        "reject_git_lfs_pointer_text_masquerading_as_wav",
        "reject_missing_empty_zero_duration_unreadable_or_structurally_invalid_wav",
        "reject_non_finite_samples_and_invalid_sample_metadata",
        "exclude_confirmed_1076_mti_sad_xx_no_audio_file",
        "inspect_every_official_mp3_or_video_mismatch_wav_counterpart",
        "tied_audio_only_majority_labels_are_ambiguous_without_a_preregistered_rule",
        "retain_every_exclusion_and_reason_in_an_immutable_quality_inventory",
        "actor_id_never_crosses_dependency_partitions",
        "sentence_identity_is_an_additional_scripted_scenario_dependency_key",
    ],
    "known_issues": [
        "1076_MTI_SAD_XX.wav_has_an_official_documented_no_audio_issue",
        "audio_raters_heard_presentation_encodings_while_feature_checks_use_wav",
        "ordinary_github_zip_contains_git_lfs_pointer_stubs_not_audio_bytes",
    ],
    "dependency_key_rules": {
        "speaker": "ActorID -> speaker, required",
        "call_session": (
            "recording session -> call_session, covered_by_higher_dependency(speaker), "
            "subject to verified nesting"
        ),
        "dialogue_dyad": "isolated utterance -> dialogue_dyad, not_applicable",
        "source_corpus": "dataset manifest ID -> source_corpus, required",
        "scripted_scenario": "sentence code -> scripted_scenario, required",
        "meeting_series": "isolated utterance -> meeting_series, not_applicable",
        "recording_site": "recording site -> recording_site, advisory and not_available",
    },
}
AMI_PROFILE_SELECTION = {
    "source_label": "public-only",
    "source_labels": [
        "participant_or_speaker_association",
        "word_and_utterance_timing",
        "transcript_boundaries",
        "turn_continuation_and_completion",
        "disfluency_and_nonverbal_transcript_markers",
        "dialogue_act_categories",
        "meeting_and_partition_membership",
    ],
    "project_label_mapping": {},
    "excluded_labels": PROJECT_OPERATIONAL_SIGNAL_ORDER,
    "access_restrictions": [
        "separate_download_authorization_required",
        "official_manual_annotation_archive_only",
        "audio_video_automatic_dome_social_role_and_speculative_emotion_material_excluded",
    ],
    "domain_limitations": [
        "manual_annotation_release_supplies_no_emotion_reference_labels",
        "annotation_only_selection_cannot_support_prosody_evaluation",
        "multi_party_meetings_do_not_validate_sales_or_customer_state_claims",
        "some_tno_participant_metadata_was_not_gathered",
        "documented_synchronization_and_dropout_limitations_remain_despite_no_media_selection",
    ],
    "permitted_research_lanes": [
        "transcript-derived turn-boundary checks",
        "speaker-balance and exchange-rate mechanics",
        "overlap and timing-schema validation when supported by released annotations",
        "dependency-group and dedup test design",
        "offline thesis limitations analysis",
    ],
    "redistribution_status": "not_permitted_from_this_project",
    "dependency_keys": DEPENDENCY_KEYS,
    "quality_rules": [
        "hash_the_exact_downloaded_archive_before_extraction",
        "hash_every_selected_extracted_file_in_stable_path_order",
        "selected_paths_remain_under_the_approved_ami_dataset_root",
        "preserve_participant_meeting_series_site_and_scenario_dependencies",
        "never_split_a_participant_or_four_meeting_series_across_an_evaluation_boundary",
        "quarantine_records_whose_required_participant_identity_cannot_be_verified",
        "retain_official_scenario_and_full_corpus_partitions_without_assigning_project_cases",
    ],
    "known_issues": [
        "local_archive_sha256_is_local_retrieval_pin_not_publisher_signed_checksum",
        "some_tno_participant_metadata_was_not_gathered",
        "documented_synchronization_and_dropout_limitations_exist",
        "speculative_emotion_annotations_are_not_generally_available",
    ],
    "dependency_key_rules": {
        "speaker": "participant ID -> speaker, required",
        "call_session": "meeting ID -> call_session, required",
        "dialogue_dyad": "multi-party meeting -> dialogue_dyad, not_applicable and never fabricated",
        "source_corpus": "dataset manifest ID -> source_corpus, required",
        "scripted_scenario": (
            "scenario identity -> scripted_scenario, required for scenario meetings and "
            "not_applicable for documented natural meetings"
        ),
        "meeting_series": (
            "four-meeting day or shared series ID -> meeting_series, required for scenario series; "
            "documented standalone non-scenario meeting -> not_applicable"
        ),
        "recording_site": "recording location -> recording_site, required",
    },
}

def _freeze_profile_value(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_profile_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_profile_value(item) for item in value)
    return value


def _thaw_profile_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_profile_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_profile_value(item) for item in value]
    return deepcopy(value)


_DATASET_PROFILES: Mapping[str, Mapping[str, Any]] = _freeze_profile_value({
    CREMA_DATASET_ID: {
        "dataset_id": CREMA_DATASET_ID,
        **deepcopy(CREMA_PROFILE_IDENTITY),
        **deepcopy(CREMA_PROFILE_SELECTION),
        "raw_source_label_map": deepcopy(CREMA_RAW_SOURCE_LABEL_MAP),
        "manifest_version": 2,
        "runtime_influence_allowed": False,
    },
    AMI_DATASET_ID: {
        "dataset_id": AMI_DATASET_ID,
        **deepcopy(AMI_PROFILE_IDENTITY),
        **deepcopy(AMI_PROFILE_SELECTION),
        "source_revision": None,
        "manifest_version": 2,
        "runtime_influence_allowed": False,
    },
})

COMPLETION_STATUSES = frozenset({"material_verification_pending", "verified"})
LOCAL_FILE_HASH_FIELDS = frozenset({
    "algorithm",
    "inventory_path",
    "inventory_sha256",
    "selected_file_count",
    "selected_byte_count",
})
HASH_INVENTORY_REFERENCE_FIELDS = frozenset({
    "schema_id",
    "schema_version",
    "algorithm",
    "inventory_path",
    "inventory_sha256",
    "selected_file_count",
    "selected_byte_count",
    "path_normalization",
    "ordering",
})
EXCLUSION_INVENTORY_FIELDS = frozenset({
    "schema_id",
    "schema_version",
    "quality_inventory_path",
    "quality_inventory_sha256",
    "included_file_count",
    "excluded_file_count",
})
HASH_INVENTORY_FIELDS = frozenset({
    "inventory_version",
    "dataset_id",
    "algorithm",
    "path_normalization",
    "ordering",
    "selected_file_count",
    "selected_byte_count",
    "files",
})
HASH_INVENTORY_FILE_FIELDS = frozenset({"path", "size_bytes", "sha256"})
HASH_INVENTORY_FILE_FIELDS_WITH_LFS = HASH_INVENTORY_FILE_FIELDS | frozenset({
    "git_lfs_oid_sha256",
})
UPPER_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
ACCESS_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CREMA_FILENAME_PATTERN = re.compile(
    r"^(?P<actor_id>\d{4})_(?P<sentence_code>[A-Z0-9]{3})_"
    r"(?P<intended_emotion_code>ANG|DIS|FEA|HAP|NEU|SAD)_"
    r"(?P<intensity_code>HI|LO|MD|XX)\.(?P<extension>wav|mp3|flv|mp4)$",
    re.IGNORECASE,
)
GIT_LFS_POINTER_SIGNATURE = b"version https://git-lfs.github.com/spec/v1"

CREMA_SELECTED_FIXED_PATHS = (
    "processedResults/summaryTable.csv",
    "finishedResponses.csv",
    "SentenceFilenames.csv",
    "README.md",
    "LICENSE.txt",
)
CREMA_AUDIO_PREFIX = "AudioWAV/"
CREMA_KNOWN_NO_AUDIO_FILE = "AudioWAV/1076_MTI_SAD_XX.wav"
CREMA_EXCLUDED_PATHS = frozenset({"VideoDemographics.csv"})
CREMA_INTENDED_EMOTION_CODE_MAP = {
    "ANG": "anger",
    "DIS": "disgust",
    "FEA": "fear",
    "HAP": "happy",
    "NEU": "neutral",
    "SAD": "sad",
}


class PublicDatasetContractError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    try:
        payload = Path(path).read_bytes()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"selected dataset file is missing or unreadable: {path}") from exc
    return hashlib.sha256(payload).hexdigest().upper()


def canonical_inventory_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def normalized_relative_path(path: Path, project_root: Path) -> str:
    try:
        resolved = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"selected dataset file is missing: {path}") from exc
    try:
        root = Path(project_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("approved project root is missing") from exc
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("selected dataset path escapes its approved root") from exc
    value = unicodedata.normalize("NFC", relative.as_posix())
    if not value or value.startswith("../"):
        raise ValueError("selected dataset path is not canonical")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("selected dataset path is not canonical")
    return value


def _normalize_lfs_oid(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Git LFS OID must be a SHA-256 string or pointer text")
    match = re.search(r"(?:^|\n)oid sha256:([0-9A-Fa-f]{64})(?:\n|$)", value)
    digest = match.group(1) if match is not None else value
    if re.fullmatch(r"[0-9A-Fa-f]{64}", digest) is None:
        raise ValueError("Git LFS OID must be a SHA-256 string or pointer text")
    return digest.upper()


def build_hash_inventory(
    *,
    dataset_id: str,
    project_root: Path,
    selected_paths: list[Path] | tuple[Path, ...],
    git_lfs_oids_by_path: Mapping[str | Path, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("dataset_id must be a non-empty string")
    root = Path(project_root)
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("approved project root is missing") from exc
    if not resolved_root.is_dir():
        raise ValueError("approved project root must be a directory")

    normalized_lfs_oids: dict[str, str] = {}
    if git_lfs_oids_by_path is not None:
        if not isinstance(git_lfs_oids_by_path, Mapping):
            raise ValueError("Git LFS OID pins must be a mapping")
        for raw_path, raw_oid in git_lfs_oids_by_path.items():
            if isinstance(raw_path, Path):
                normalized_path = normalized_relative_path(raw_path, resolved_root)
            elif isinstance(raw_path, str):
                normalized_path = _normalized_inventory_path(raw_path)
            else:
                raise ValueError("Git LFS OID path keys must be paths or strings")
            if normalized_path in normalized_lfs_oids:
                raise ValueError("duplicate Git LFS OID path")
            normalized_lfs_oids[normalized_path] = _normalize_lfs_oid(raw_oid)

    entries: list[dict[str, Any]] = []
    normalized_paths: set[str] = set()
    casefold_paths: set[str] = set()
    for selected_path in selected_paths:
        path = Path(selected_path)
        normalized_path = normalized_relative_path(path, resolved_root)
        if normalized_path in normalized_paths:
            raise ValueError("hash inventory contains a duplicate normalized path")
        casefold_path = normalized_path.casefold()
        if casefold_path in casefold_paths:
            raise ValueError("hash inventory contains a case-fold path collision")
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"selected dataset file is missing: {path}") from exc
        if not resolved.is_file():
            raise ValueError(f"selected dataset path is not a file: {normalized_path}")
        size_bytes = resolved.stat().st_size
        digest = sha256_file(resolved)
        entry: dict[str, Any] = {
            "path": normalized_path,
            "size_bytes": size_bytes,
            "sha256": digest,
        }
        if normalized_path in normalized_lfs_oids:
            lfs_digest = normalized_lfs_oids[normalized_path]
            if lfs_digest != digest:
                raise ValueError(
                    f"Git LFS OID does not match the selected file hash: {normalized_path}"
                )
            entry["git_lfs_oid_sha256"] = lfs_digest
        entries.append(entry)
        normalized_paths.add(normalized_path)
        casefold_paths.add(casefold_path)

    unbound_lfs_paths = set(normalized_lfs_oids) - normalized_paths
    if unbound_lfs_paths:
        raise ValueError(
            "Git LFS OID pin does not name a selected file: "
            + sorted(unbound_lfs_paths)[0]
        )
    entries.sort(key=lambda item: item["path"])
    return {
        "inventory_version": 1,
        "dataset_id": dataset_id,
        "algorithm": "SHA-256",
        "path_normalization": "project-relative-posix-nfc",
        "ordering": "ordinal-by-normalized-path",
        "selected_file_count": len(entries),
        "selected_byte_count": sum(item["size_bytes"] for item in entries),
        "files": entries,
    }


def validate_wav_file(path: Path) -> dict[str, Any]:
    wav_path = Path(path)
    try:
        size_bytes = wav_path.stat().st_size
        with wav_path.open("rb") as source:
            prefix = source.read(max(128, len(GIT_LFS_POINTER_SIGNATURE)))
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"WAV file is missing or unreadable: {wav_path}") from exc
    if prefix.startswith(GIT_LFS_POINTER_SIGNATURE):
        raise ValueError(f"Git LFS pointer is not WAV material: {wav_path}")
    if size_bytes < 44:
        raise ValueError(f"WAV file is smaller than a valid RIFF/WAVE header: {wav_path}")

    try:
        with wave.open(str(wav_path), "rb") as source:
            channel_count = source.getnchannels()
            sample_width_bytes = source.getsampwidth()
            sample_rate_hz = source.getframerate()
            frame_count = source.getnframes()
            compression_type = source.getcomptype()
            if compression_type != "NONE":
                raise ValueError("unsupported WAV encoding; verified material must be PCM")
            if channel_count <= 0:
                raise ValueError("WAV channel metadata must be positive")
            if sample_width_bytes not in {1, 2, 3, 4}:
                raise ValueError("WAV sample-width metadata is unsupported")
            if sample_rate_hz <= 0:
                raise ValueError("WAV sample-rate metadata must be positive")
            if frame_count <= 0:
                raise ValueError("WAV frame count must be positive; zero-duration content is invalid")
            expected_frame_bytes = frame_count * channel_count * sample_width_bytes
            try:
                frame_bytes = source.readframes(frame_count)
            except (OSError, EOFError, wave.Error) as exc:
                raise ValueError("WAV contains unreadable frames") from exc
    except ValueError:
        raise
    except wave.Error as exc:
        message = str(exc).lower()
        if "unknown format" in message:
            raise ValueError("unsupported WAV encoding; verified material must be PCM") from exc
        raise ValueError(f"invalid WAV metadata: {exc}") from exc
    except (EOFError, OSError) as exc:
        raise ValueError(f"WAV file is unreadable or structurally invalid: {wav_path}") from exc

    if len(frame_bytes) != expected_frame_bytes:
        raise ValueError("WAV contains unreadable frames")
    duration_seconds = frame_count / sample_rate_hz
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("WAV has zero-duration or non-finite duration")
    return {
        "channel_count": channel_count,
        "sample_width_bytes": sample_width_bytes,
        "sample_rate_hz": sample_rate_hz,
        "frame_count": frame_count,
        "duration_seconds": duration_seconds,
        "encoding": "PCM",
    }


def parse_crema_filename(path_or_name: str | Path) -> dict[str, str]:
    filename = Path(path_or_name).name
    match = CREMA_FILENAME_PATTERN.fullmatch(filename)
    if match is None:
        raise ValueError(f"invalid CREMA-D filename: {filename}")
    values = {key: value.upper() for key, value in match.groupdict().items()}
    values["extension"] = values["extension"].lower()
    values["intended_source_label"] = CREMA_INTENDED_EMOTION_CODE_MAP[
        values["intended_emotion_code"]
    ]
    values["intended_label_role"] = "prompt_metadata_only"
    return values


def _relative_to_exact_root(path: Path, root: Path, *, field: str) -> str:
    try:
        resolved = Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{field} is missing: {path}") from exc
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field} escapes its approved root") from exc
    value = unicodedata.normalize("NFC", relative.as_posix())
    if not value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"{field} is not canonical")
    return value


def _first_present_field(
    row: Mapping[str, str | None],
    candidates: tuple[str, ...],
) -> tuple[str | None, str | None]:
    casefold_names = {
        key.casefold(): key
        for key in row
        if isinstance(key, str)
    }
    for candidate in candidates:
        source_key = casefold_names.get(candidate.casefold())
        if source_key is None:
            continue
        value = row.get(source_key)
        return source_key, value.strip() if isinstance(value, str) else None
    return None, None


def _parse_vote_value(value: str) -> dict[str, int]:
    normalized = value.strip().upper()
    if not normalized:
        return {}
    if normalized in CREMA_RAW_SOURCE_LABEL_MAP:
        return {normalized: 1}
    pairs = re.findall(r"\b([ADF HNS])\s*[:=]\s*(\d+)\b", normalized.replace(" ", ""))
    if not pairs:
        raise ValueError(f"invalid CREMA-D audio-only source label: {value}")
    counts: dict[str, int] = {}
    for code, count_text in pairs:
        code = code.strip()
        if code not in CREMA_RAW_SOURCE_LABEL_MAP:
            raise ValueError(f"invalid CREMA-D audio-only source label: {code}")
        count = int(count_text)
        if count < 0:
            raise ValueError("CREMA-D vote counts must be nonnegative")
        counts[code] = counts.get(code, 0) + count
    return counts


def _read_crema_audio_only_votes(path: Path) -> dict[str, dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames is None:
                raise ValueError("finishedResponses.csv has invalid metadata")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError("finishedResponses.csv is unreadable or invalid") from exc

    votes_by_wav: dict[str, dict[str, Any]] = {}
    filename_candidates = (
        "FileName",
        "Filename",
        "file_name",
        "AudioFile",
        "audio_file",
        "Stimulus",
        "Clip",
    )
    modality_candidates = (
        "Modality",
        "Presentation",
        "presentation_modality",
        "MediaType",
    )
    label_candidates = (
        "Response",
        "AudioVote",
        "audio_vote",
        "Vote",
        "Label",
        "Emotion",
        "Answer",
    )
    for row_index, row in enumerate(rows, start=2):
        filename_column, filename_value = _first_present_field(row, filename_candidates)
        if filename_column is None or not filename_value:
            continue
        modality_column, modality_value = _first_present_field(row, modality_candidates)
        label_column, label_value = _first_present_field(row, label_candidates)
        modality = (modality_value or "").strip().casefold().replace("_", "-")
        if modality_column is not None and modality:
            audio_only = modality in {
                "audio",
                "audio-only",
                "audio only",
                "sound",
                "a",
            }
        else:
            audio_only = label_column is not None and "audio" in label_column.casefold()
        if not audio_only:
            continue
        if label_column is None:
            count_columns = {
                code: _first_present_field(row, (code,))[1]
                for code in CREMA_RAW_SOURCE_LABEL_MAP
            }
            present_counts = {
                code: int(value)
                for code, value in count_columns.items()
                if isinstance(value, str) and value.strip()
            }
            if not present_counts:
                continue
            raw_votes = present_counts
            label_column = "A/D/F/H/N/S"
        else:
            raw_votes = _parse_vote_value(label_value or "")
        try:
            filename_metadata = parse_crema_filename(filename_value)
        except ValueError as exc:
            raise ValueError(
                f"finishedResponses.csv row {row_index} has an invalid CREMA-D filename"
            ) from exc
        wav_name = (
            f"{filename_metadata['actor_id']}_{filename_metadata['sentence_code']}_"
            f"{filename_metadata['intended_emotion_code']}_"
            f"{filename_metadata['intensity_code']}.wav"
        )
        record = votes_by_wav.setdefault(
            wav_name,
            {
                "vote_distribution": {},
                "source_columns": set(),
                "audio_presentation_encodings": set(),
            },
        )
        record["source_columns"].add(label_column)
        record["audio_presentation_encodings"].add(
            filename_metadata["extension"]
        )
        for code, count in raw_votes.items():
            if code not in CREMA_RAW_SOURCE_LABEL_MAP:
                raise ValueError(
                    f"finishedResponses.csv row {row_index} has an invalid source label"
                )
            if type(count) is not int or count < 0:
                raise ValueError(
                    f"finishedResponses.csv row {row_index} has an invalid vote count"
                )
            distribution = record["vote_distribution"]
            distribution[code] = distribution.get(code, 0) + count

    normalized: dict[str, dict[str, Any]] = {}
    for wav_name, record in votes_by_wav.items():
        distribution = {
            code: record["vote_distribution"][code]
            for code in sorted(record["vote_distribution"])
            if record["vote_distribution"][code] > 0
        }
        total_votes = sum(distribution.values())
        max_votes = max(distribution.values(), default=0)
        winners = [
            code
            for code, count in distribution.items()
            if count == max_votes and max_votes > 0
        ]
        ambiguous = len(winners) != 1
        raw_source_label = winners[0] if not ambiguous else None
        normalized[wav_name] = {
            "raw_source_label": raw_source_label,
            "normalized_source_label": (
                CREMA_RAW_SOURCE_LABEL_MAP[raw_source_label]
                if raw_source_label is not None
                else None
            ),
            "source_column": (
                sorted(record["source_columns"])[0]
                if len(record["source_columns"]) == 1
                else sorted(record["source_columns"])
            ),
            "vote_distribution": distribution,
            "agreement": (max_votes / total_votes if total_votes else None),
            "ambiguous": ambiguous,
            "abstained": ambiguous,
            "ambiguity_reason": (
                None
                if not ambiguous
                else (
                    "tied_audio_only_majority_labels"
                    if len(winners) > 1
                    else "missing_audio_only_perceived_label"
                )
            ),
            "audio_presentation_encodings": sorted(
                record["audio_presentation_encodings"]
            ),
            "source_file_path": "finishedResponses.csv",
        }
    return normalized


def _missing_crema_source_label_evidence() -> dict[str, Any]:
    return {
        "raw_source_label": None,
        "normalized_source_label": None,
        "source_column": None,
        "vote_distribution": {},
        "agreement": None,
        "ambiguous": True,
        "abstained": True,
        "ambiguity_reason": "missing_audio_only_perceived_label",
        "audio_presentation_encodings": [],
        "source_file_path": "finishedResponses.csv",
    }


def _crema_mismatch_counterparts(summary_path: Path) -> list[str]:
    try:
        text = summary_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ValueError("processedResults/summaryTable.csv is unreadable") from exc
    names = {
        match.group(0)
        for match in re.finditer(
            r"\b\d{4}_[A-Z0-9]{3}_(?:ANG|DIS|FEA|HAP|NEU|SAD)_"
            r"(?:HI|LO|MD|XX)\.(?:wav|mp3|flv|mp4)\b",
            text,
            flags=re.IGNORECASE,
        )
    }
    counterparts: set[str] = set()
    for name in names:
        parsed = parse_crema_filename(name)
        counterparts.add(
            f"{CREMA_AUDIO_PREFIX}{parsed['actor_id']}_{parsed['sentence_code']}_"
            f"{parsed['intended_emotion_code']}_{parsed['intensity_code']}.wav"
        )
    return sorted(counterparts)


def validate_crema_material(
    crema_root: Path,
    *,
    project_root: Path | None = None,
    selected_paths: list[Path] | tuple[Path, ...] | None = None,
    git_lfs_oids_by_path: Mapping[str | Path, str] | None = None,
) -> dict[str, Any]:
    try:
        root = Path(crema_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("CREMA-D root is missing") from exc
    if not root.is_dir():
        raise ValueError("CREMA-D root must be a directory")
    inventory_root = (
        Path(project_root).resolve(strict=True)
        if project_root is not None
        else root
    )

    fixed_paths: list[Path] = []
    for relative_path in CREMA_SELECTED_FIXED_PATHS:
        candidate = root.joinpath(*relative_path.split("/"))
        if not candidate.is_file():
            raise ValueError(f"missing selected file: {relative_path}")
        if candidate.stat().st_size <= 0:
            raise ValueError(f"selected metadata file is empty: {relative_path}")
        fixed_paths.append(candidate)

    votes_by_wav = _read_crema_audio_only_votes(root / "finishedResponses.csv")
    mismatch_counterparts = _crema_mismatch_counterparts(
        root / "processedResults" / "summaryTable.csv"
    )
    audio_root = root / "AudioWAV"
    if not audio_root.is_dir():
        raise ValueError("missing selected file: AudioWAV/")

    quality_by_path: dict[str, dict[str, Any]] = {}
    selected_audio_paths: list[Path] = []
    for wav_path in sorted(
        (path for path in audio_root.rglob("*") if path.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative_path = _relative_to_exact_root(
            wav_path,
            root,
            field="CREMA-D material path",
        )
        if wav_path.suffix.casefold() != ".wav":
            quality_by_path[relative_path] = {
                "path": relative_path,
                "classification": "crema_audio_directory_non_wav",
                "disposition": "excluded",
                "reason": "frozen_selection_requires_wav",
                "selected_file_path": None,
                "details": {},
            }
            continue
        filename_metadata = parse_crema_filename(wav_path.name)
        if relative_path == CREMA_KNOWN_NO_AUDIO_FILE:
            try:
                validate_wav_file(wav_path)
            except ValueError as exc:
                if "Git LFS pointer" in str(exc):
                    raise
                objective_failure = "objective_wav_validation_failed"
            else:
                raise ValueError(
                    "official known no-audio issue was not confirmed by the pinned release"
                )
            quality_by_path[relative_path] = {
                "path": relative_path,
                "classification": "crema_wav",
                "disposition": "excluded",
                "reason": "official_known_no_audio_issue",
                "selected_file_path": None,
                "details": {
                    "filename_metadata": filename_metadata,
                    "official_issue": "1076_MTI_SAD_XX.wav_has_an_official_documented_no_audio_issue",
                    "objective_failure_confirmed": True,
                    "objective_failure": objective_failure,
                },
            }
            continue
        wav_metadata = validate_wav_file(wav_path)
        source_label_evidence = deepcopy(
            votes_by_wav.get(
                wav_path.name,
                _missing_crema_source_label_evidence(),
            )
        )
        quality_by_path[relative_path] = {
            "path": relative_path,
            "classification": "crema_pcm_wav",
            "disposition": "included",
            "reason": (
                "official_mismatch_wav_counterpart_objectively_validated"
                if relative_path in mismatch_counterparts
                else "frozen_audio_wav_selection"
            ),
            "selected_file_path": normalized_relative_path(
                wav_path,
                inventory_root,
            ),
            "details": {
                "filename_metadata": filename_metadata,
                "wav_metadata": wav_metadata,
                "source_label_evidence": source_label_evidence,
                "dependency_keys": {
                    "speaker": filename_metadata["actor_id"],
                    "source_corpus": CREMA_DATASET_ID,
                    "scripted_scenario": filename_metadata["sentence_code"],
                },
            },
        }
        selected_audio_paths.append(wav_path)

    for counterpart in mismatch_counterparts:
        if counterpart == CREMA_KNOWN_NO_AUDIO_FILE:
            continue
        if counterpart not in quality_by_path:
            raise ValueError(
                f"official mismatch WAV counterpart is missing: {counterpart}"
            )
        if quality_by_path[counterpart]["disposition"] != "included":
            raise ValueError(
                f"official mismatch WAV counterpart failed objective validation: {counterpart}"
            )

    if CREMA_KNOWN_NO_AUDIO_FILE not in quality_by_path:
        raise ValueError(f"missing selected file: {CREMA_KNOWN_NO_AUDIO_FILE}")
    for wav_name in votes_by_wav:
        relative_path = f"{CREMA_AUDIO_PREFIX}{wav_name}"
        if relative_path not in quality_by_path:
            raise ValueError(f"missing selected file: {relative_path}")

    expected_selected_paths = [*fixed_paths, *selected_audio_paths]
    expected_dataset_relative = {
        _relative_to_exact_root(path, root, field="selected CREMA-D file")
        for path in expected_selected_paths
    }
    if selected_paths is not None:
        provided_dataset_relative: set[str] = set()
        for path in selected_paths:
            try:
                relative_path = _relative_to_exact_root(
                    Path(path),
                    root,
                    field="selected CREMA-D file",
                )
            except ValueError as exc:
                raise ValueError(f"extra selected file: {path}") from exc
            if relative_path in provided_dataset_relative:
                raise ValueError(f"extra selected file: {relative_path}")
            provided_dataset_relative.add(relative_path)
        missing = expected_dataset_relative - provided_dataset_relative
        if missing:
            raise ValueError(f"missing selected file: {sorted(missing)[0]}")
        extra = provided_dataset_relative - expected_dataset_relative
        if extra:
            raise ValueError(f"extra selected file: {sorted(extra)[0]}")
        expected_selected_paths = [Path(path) for path in selected_paths]

    for fixed_path in fixed_paths:
        relative_path = _relative_to_exact_root(
            fixed_path,
            root,
            field="selected CREMA-D file",
        )
        quality_by_path[relative_path] = {
            "path": relative_path,
            "classification": "crema_release_metadata",
            "disposition": "included",
            "reason": "frozen_fixed_selection",
            "selected_file_path": normalized_relative_path(
                fixed_path,
                inventory_root,
            ),
            "details": {},
        }

    for file_path in sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative_path = _relative_to_exact_root(
            file_path,
            root,
            field="CREMA-D material path",
        )
        if relative_path in quality_by_path:
            continue
        if relative_path in CREMA_EXCLUDED_PATHS:
            classification = "crema_demographic_metadata"
            reason = "excluded_demographic_metadata"
        else:
            classification = "crema_unselected_release_material"
            reason = "outside_frozen_selection"
        quality_by_path[relative_path] = {
            "path": relative_path,
            "classification": classification,
            "disposition": "excluded",
            "reason": reason,
            "selected_file_path": None,
            "details": {},
        }

    hash_inventory = build_hash_inventory(
        dataset_id=CREMA_DATASET_ID,
        project_root=inventory_root,
        selected_paths=expected_selected_paths,
        git_lfs_oids_by_path=git_lfs_oids_by_path,
    )
    if git_lfs_oids_by_path is not None:
        missing_lfs_evidence = [
            entry["path"]
            for entry in hash_inventory["files"]
            if (
                entry["path"].startswith(f"{CREMA_AUDIO_PREFIX}")
                or f"/{CREMA_AUDIO_PREFIX}" in entry["path"]
            )
            and "git_lfs_oid_sha256" not in entry
        ]
        if missing_lfs_evidence:
            raise ValueError(
                "missing selected CREMA-D Git LFS OID evidence: "
                + missing_lfs_evidence[0]
            )
    quality_items = [
        quality_by_path[path]
        for path in sorted(quality_by_path)
    ]
    included_file_count = sum(
        item["disposition"] == "included"
        for item in quality_items
    )
    excluded_file_count = sum(
        item["disposition"] == "excluded"
        for item in quality_items
    )
    quality_inventory = {
        "quality_inventory_version": 1,
        "dataset_id": CREMA_DATASET_ID,
        "included_file_count": included_file_count,
        "excluded_file_count": excluded_file_count,
        "items": quality_items,
        "limitations": [
            "raters_heard_audio_presentation_encodings_while_feature_verification_uses_corresponding_wav_files",
            "filename_intended_emotion_is_prompt_metadata_only_and_never_fills_a_missing_perceived_label",
            "filename_agreement_cannot_override_an_official_mismatch_or_objective_content_or_duration_failure",
        ],
        "dependency_quarantine": [],
        "source_metadata": {
            "official_mismatch_wav_counterparts": mismatch_counterparts,
            "advertised_utterance_count_used": False,
            "selected_encoding": "wav",
            "source_label_rows": "finishedResponses.csv audio-only rows",
        },
    }
    return {
        "hash_inventory": hash_inventory,
        "quality_inventory": quality_inventory,
    }


AMI_SELECTED_CLASSIFICATIONS = frozenset({
    "manual_nxt_metadata",
    "speaker_aligned_orthographic_transcript",
    "timing_link",
    "dialogue_act",
    "official_partition_metadata",
})
AMI_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".flac", ".sph", ".m4a"})
AMI_VIDEO_SUFFIXES = frozenset({".avi", ".mp4", ".mpeg", ".mpg", ".mov", ".wmv"})
AMI_POTENTIALLY_SELECTED_SUFFIXES = frozenset({
    ".xml",
    ".nxt",
    ".json",
    ".csv",
    ".txt",
    ".list",
})


def _normalized_archive_member_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("AMI archive member path is invalid")
    normalized_separators = value.replace("\\", "/")
    if (
        normalized_separators.startswith("/")
        or PurePosixPath(normalized_separators).is_absolute()
        or PureWindowsPath(value).drive
        or re.match(r"^[A-Za-z]:", normalized_separators)
    ):
        raise ValueError("AMI archive path escape or absolute path")
    is_directory = normalized_separators.endswith("/")
    raw_parts = normalized_separators.rstrip("/").split("/")
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("AMI archive path escape or dot segment")
    normalized = unicodedata.normalize("NFC", "/".join(raw_parts))
    if not normalized or normalized.startswith("../"):
        raise ValueError("AMI archive path escape")
    return normalized + ("/" if is_directory else "")


def classify_ami_member(path: str) -> dict[str, Any]:
    normalized = _normalized_archive_member_path(path)
    if normalized.endswith("/"):
        return {
            "classification": "directory",
            "selected": False,
            "reason": "archive_directory",
        }
    pure = PurePosixPath(normalized)
    suffix = pure.suffix.casefold()
    components = [part.casefold() for part in pure.parts]
    joined = "/".join(components)

    if suffix in AMI_AUDIO_SUFFIXES or "audio" in components:
        classification = "audio"
    elif suffix in AMI_VIDEO_SUFFIXES or "video" in components:
        classification = "video"
    elif any(
        marker in components or marker in joined
        for marker in ("automatic", "ami_public_auto", "/asr", "asr/")
    ):
        classification = "automatic_annotation"
    elif "dome" in joined:
        classification = "dome"
    elif any(
        marker in joined
        for marker in ("socialrole", "social_role", "social-role")
    ):
        classification = "social_role"
    elif any(
        marker in joined
        for marker in ("emotion", "affect", "sentiment")
    ):
        classification = "speculative_emotion"
    elif any(
        marker in joined
        for marker in ("dialogueact", "dialogue_act", "dialogue-act")
    ):
        classification = "dialogue_act"
    elif any(
        marker in joined
        for marker in ("partition", "split-definition", "full-corpus")
    ):
        classification = "official_partition_metadata"
    elif any(
        marker in components or marker in joined
        for marker in ("words", "transcript", "orthograph")
    ):
        classification = "speaker_aligned_orthographic_transcript"
    elif any(
        marker in components or marker in joined
        for marker in ("segments", "timing", "time-link", "timelink")
    ):
        classification = "timing_link"
    elif any(
        marker in joined
        for marker in (
            "corpusresources",
            "corpus-resources",
            "metadata",
            "meetings.xml",
            "participants.xml",
            "speakers.xml",
        )
    ):
        classification = "manual_nxt_metadata"
    elif pure.name.casefold().startswith(("readme", "license", "copying")):
        classification = "documentation"
    elif suffix in AMI_POTENTIALLY_SELECTED_SUFFIXES:
        raise ValueError(f"unclassified AMI annotation candidate: {normalized}")
    else:
        classification = "unselected_release_material"

    selected = classification in AMI_SELECTED_CLASSIFICATIONS
    return {
        "classification": classification,
        "selected": selected,
        "reason": (
            "selected_manual_annotation_material"
            if selected
            else f"excluded_{classification}"
        ),
    }


def _zip_info_is_symlink(info: zipfile.ZipInfo) -> bool:
    unix_mode = info.external_attr >> 16
    return (unix_mode & 0o170000) == 0o120000


def inspect_ami_archive(
    archive_path: Path,
    extract_root: Path,
) -> dict[str, Any]:
    archive = Path(archive_path)
    archive_sha256 = sha256_file(archive)
    try:
        archive_size_bytes = archive.stat().st_size
    except OSError as exc:
        raise ValueError("AMI archive is missing or unreadable") from exc
    extraction_root = Path(extract_root).resolve(strict=False)

    structurally_valid_members: list[tuple[zipfile.ZipInfo, str]] = []
    validated_members: list[dict[str, Any]] = []
    normalized_paths: set[str] = set()
    casefold_paths: set[str] = set()
    try:
        with zipfile.ZipFile(archive, "r") as source:
            for info in source.infolist():
                normalized_path = _normalized_archive_member_path(info.filename)
                collision_key = normalized_path.rstrip("/")
                if collision_key in normalized_paths:
                    raise ValueError("AMI archive contains a duplicate destination")
                casefold_key = collision_key.casefold()
                if casefold_key in casefold_paths:
                    raise ValueError("AMI archive contains a case-fold destination collision")
                if _zip_info_is_symlink(info):
                    raise ValueError(f"AMI archive contains a symlink entry: {normalized_path}")
                destination = extraction_root.joinpath(
                    *normalized_path.rstrip("/").split("/")
                )
                try:
                    destination.resolve(strict=False).relative_to(extraction_root)
                except ValueError as exc:
                    raise ValueError("AMI archive path escape") from exc
                structurally_valid_members.append((info, normalized_path))
                normalized_paths.add(collision_key)
                casefold_paths.add(casefold_key)

            destination_tree: dict[str, tuple[str, str]] = {}
            for info, normalized_path in structurally_valid_members:
                member_path = normalized_path.rstrip("/")
                parts = member_path.split("/")
                for index in range(1, len(parts) + 1):
                    node_path = "/".join(parts[:index])
                    node_kind = (
                        "directory"
                        if index < len(parts) or info.is_dir()
                        else "file"
                    )
                    casefold_key = node_path.casefold()
                    existing = destination_tree.get(casefold_key)
                    if existing is None:
                        destination_tree[casefold_key] = (node_path, node_kind)
                        continue
                    existing_path, existing_kind = existing
                    if existing_path != node_path:
                        raise ValueError(
                            "AMI archive case-fold file/descendant prefix conflict"
                        )
                    if existing_kind != node_kind:
                        raise ValueError(
                            "AMI archive file/descendant prefix conflict"
                        )

            for info, normalized_path in structurally_valid_members:
                classification = classify_ami_member(normalized_path)
                member = {
                    "path": normalized_path,
                    "classification": classification["classification"],
                    "selected": classification["selected"],
                    "reason": classification["reason"],
                }
                validated_members.append(member)
            validated_members.sort(key=lambda item: item["path"])
    except zipfile.BadZipFile as exc:
        raise ValueError("AMI archive is not a readable ZIP file") from exc
    except OSError as exc:
        raise ValueError("AMI archive inspection failed") from exc

    return {
        "archive_sha256": archive_sha256,
        "archive_size_bytes": archive_size_bytes,
        "members": validated_members,
    }


def _expected_ami_extraction_tree(
    members: list[dict[str, Any]],
) -> dict[str, str]:
    expected: dict[str, str] = {}
    for member in members:
        path = member["path"].rstrip("/")
        if member["classification"] == "directory":
            expected[path] = "directory"
        elif member["selected"]:
            expected[path] = "file"
        else:
            continue
        parts = path.split("/")
        for index in range(1, len(parts)):
            ancestor = "/".join(parts[:index])
            existing = expected.get(ancestor)
            if existing == "file":
                raise ValueError("AMI archive file/descendant prefix conflict")
            expected[ancestor] = "directory"
    return expected


def _validate_preexisting_ami_extraction_root(
    extraction_root: Path,
    expected_tree: dict[str, str],
) -> None:
    if not extraction_root.exists():
        return
    if not extraction_root.is_dir() or extraction_root.is_symlink():
        raise ValueError("pre-existing extraction path conflict")
    existing_by_casefold: dict[str, tuple[str, str]] = {}
    for path in sorted(
        extraction_root.rglob("*"),
        key=lambda item: item.relative_to(extraction_root).as_posix(),
    ):
        relative = unicodedata.normalize(
            "NFC",
            path.relative_to(extraction_root).as_posix(),
        )
        kind = "directory" if path.is_dir() and not path.is_symlink() else "file"
        casefold_path = relative.casefold()
        prior = existing_by_casefold.get(casefold_path)
        if prior is not None and prior[0] != relative:
            raise ValueError("pre-existing extraction path conflict")
        existing_by_casefold[casefold_path] = (relative, kind)
    expected_casefold = {
        path.casefold(): (path, kind)
        for path, kind in expected_tree.items()
    }
    for casefold_path, (relative, kind) in existing_by_casefold.items():
        expected = expected_casefold.get(casefold_path)
        if expected is None or expected != (relative, kind):
            raise ValueError("pre-existing extraction path conflict")


def _fresh_absent_sibling_path(parent: Path, prefix: str) -> Path:
    with tempfile.NamedTemporaryFile(
        dir=parent,
        prefix=prefix,
        delete=False,
    ) as marker:
        path = Path(marker.name)
    path.unlink()
    return path


def safe_extract_ami_archive(
    archive_path: Path,
    extract_root: Path,
) -> dict[str, Any]:
    archive = Path(archive_path)
    extraction_root = Path(extract_root).resolve(strict=False)
    inspection = inspect_ami_archive(archive, extraction_root)
    if sha256_file(archive) != inspection["archive_sha256"]:
        raise ValueError("AMI archive changed after validation and before extraction")
    expected_tree = _expected_ami_extraction_tree(inspection["members"])
    _validate_preexisting_ami_extraction_root(extraction_root, expected_tree)
    extraction_parent = extraction_root.parent
    extraction_parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(
        dir=extraction_parent,
        prefix=f".{extraction_root.name}.staging.",
    ))
    backup_root: Path | None = None
    members_by_path = {
        member["path"]: member
        for member in inspection["members"]
    }
    try:
        with zipfile.ZipFile(archive, "r") as source:
            infos_by_path = {
                _normalized_archive_member_path(info.filename): info
                for info in source.infolist()
            }
            for normalized_path in sorted(members_by_path):
                member = members_by_path[normalized_path]
                info = infos_by_path[normalized_path]
                destination = staging_root.joinpath(
                    *normalized_path.rstrip("/").split("/")
                )
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if not member["selected"]:
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    destination.resolve(strict=False).relative_to(staging_root)
                except ValueError as exc:
                    raise ValueError("AMI extraction destination escaped its exact root") from exc
                if destination.is_symlink():
                    raise ValueError("AMI extraction destination is a symlink")
                with source.open(info, "r") as member_source, destination.open("wb") as output:
                    for chunk in iter(lambda: member_source.read(1024 * 1024), b""):
                        output.write(chunk)
        if sha256_file(archive) != inspection["archive_sha256"]:
            raise ValueError("AMI archive changed during extraction")
        for relative_path, kind in expected_tree.items():
            candidate = staging_root.joinpath(*relative_path.split("/"))
            if kind == "file" and not candidate.is_file():
                raise ValueError("AMI staged extraction is incomplete")
            if kind == "directory" and not candidate.is_dir():
                raise ValueError("AMI staged extraction directory is missing")
        if extraction_root.exists():
            backup_root = _fresh_absent_sibling_path(
                extraction_parent,
                f".{extraction_root.name}.backup.",
            )
            os.replace(extraction_root, backup_root)
        try:
            os.replace(staging_root, extraction_root)
        except OSError:
            if backup_root is not None and not extraction_root.exists():
                os.replace(backup_root, extraction_root)
                backup_root = None
            raise
        if backup_root is not None:
            shutil.rmtree(backup_root)
            backup_root = None
    except zipfile.BadZipFile as exc:
        raise ValueError("AMI archive extraction failed") from exc
    except OSError as exc:
        raise ValueError("AMI archive extraction failed") from exc
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)
        if backup_root is not None and backup_root.exists():
            if not extraction_root.exists():
                os.replace(backup_root, extraction_root)
            elif backup_root.exists():
                shutil.rmtree(backup_root, ignore_errors=True)
    return inspection


def _xml_local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1].casefold()


def _ami_metadata_from_xml(path: Path) -> dict[str, set[str]]:
    values = {
        "participants": set(),
        "meetings": set(),
        "meeting_series": set(),
        "recording_sites": set(),
        "scenarios": set(),
    }
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise ValueError(f"AMI selected annotation XML is unreadable: {path}") from exc
    for element in root.iter():
        tag = _xml_local_name(element.tag)
        attributes = {
            _xml_local_name(key): value.strip()
            for key, value in element.attrib.items()
            if isinstance(value, str) and value.strip()
        }
        for key in ("participant", "participantid", "speaker", "speakerid", "agent", "nxt_agent"):
            if key in attributes:
                values["participants"].add(attributes[key])
        if tag in {"participant", "speaker", "person"} and "id" in attributes:
            values["participants"].add(attributes["id"])
        for key in ("meeting", "meetingid", "meeting_id"):
            if key in attributes:
                values["meetings"].add(attributes[key])
        if tag == "meeting" and "id" in attributes:
            values["meetings"].add(attributes["id"])
        for key in ("series", "meetingseries", "meeting_series"):
            if key in attributes:
                values["meeting_series"].add(attributes[key])
        for key in ("site", "recordingsite", "recording_site", "location"):
            if key in attributes:
                values["recording_sites"].add(attributes[key])
        for key in ("scenario", "scenarioid", "scenario_id"):
            if key in attributes:
                values["scenarios"].add(attributes[key])
    return values


def _ami_partition_definition(
    path: Path,
    *,
    project_relative_path: str,
) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"AMI partition metadata is unreadable: {path}") from exc
    meeting_ids: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in re.split(r"[\s,]+", line):
            if re.fullmatch(r"[A-Z]{2,4}\d{4}[a-z]?", token) is None:
                raise ValueError(
                    f"AMI partition metadata line {line_number} has an invalid meeting ID"
                )
            meeting_ids.add(token)
    if not meeting_ids:
        raise ValueError("AMI partition metadata has no official meeting membership")
    partition_id = path.stem
    normalized_identity = partition_id.casefold().replace("_", "-")
    if "scenario" in normalized_identity:
        partition_type = "scenario"
    elif "full" in normalized_identity and "corpus" in normalized_identity:
        partition_type = "full_corpus"
    else:
        raise ValueError(
            f"AMI partition metadata type is not approved: {partition_id}"
        )
    return {
        "partition_id": partition_id,
        "partition_type": partition_type,
        "source_file_path": project_relative_path,
        "meeting_ids": sorted(meeting_ids),
    }


def _require_complete_ami_partition_definitions(
    definitions: list[dict[str, Any]],
) -> None:
    signatures = [
        (
            definition["partition_id"],
            definition["partition_type"],
            definition["source_file_path"],
            tuple(definition["meeting_ids"]),
        )
        for definition in definitions
    ]
    if len(signatures) != len(set(signatures)):
        raise ValueError("duplicate AMI partition definition")
    partition_ids = [
        definition["partition_id"]
        for definition in definitions
    ]
    if len(partition_ids) != len(set(partition_ids)):
        raise ValueError("duplicate AMI partition ID")
    source_paths = [
        definition["source_file_path"]
        for definition in definitions
    ]
    if len(source_paths) != len(set(source_paths)):
        raise ValueError("duplicate AMI partition source path")
    partition_types = {
        definition["partition_type"]
        for definition in definitions
    }
    if partition_types != {"scenario", "full_corpus"}:
        raise ValueError(
            "AMI partition definition types must be exactly scenario and full_corpus"
        )


def validate_ami_material(
    extract_root: Path,
    *,
    archive_path: Path,
    extraction: Mapping[str, Any],
    project_root: Path | None = None,
) -> dict[str, Any]:
    try:
        root = Path(extract_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("AMI extraction root is missing") from exc
    if not root.is_dir():
        raise ValueError("AMI extraction root must be a directory")
    archive = Path(archive_path).resolve(strict=True)
    inventory_root = (
        Path(project_root).resolve(strict=True)
        if project_root is not None
        else root.parent
    )
    if not isinstance(extraction, Mapping):
        raise ValueError("AMI extraction evidence must be a mapping")
    if extraction.get("archive_sha256") != sha256_file(archive):
        raise ValueError("AMI archive hash changed after extraction")
    members = extraction.get("members")
    if not isinstance(members, list):
        raise ValueError("AMI extraction evidence members must be a list")

    selected_paths: list[Path] = [archive]
    quality_items: list[dict[str, Any]] = [{
        "path": normalized_relative_path(archive, inventory_root),
        "classification": "downloaded_archive",
        "disposition": "included",
        "reason": "archive_hashed_before_extraction",
        "selected_file_path": normalized_relative_path(
            archive,
            inventory_root,
        ),
        "details": {
            "archive_sha256": extraction["archive_sha256"],
            "archive_size_bytes": extraction["archive_size_bytes"],
        },
    }]
    dependency_quarantine: list[dict[str, str]] = []
    source_values = {
        "participants": set(),
        "meetings": set(),
        "meeting_series": set(),
        "recording_sites": set(),
        "scenarios": set(),
    }
    partition_paths: list[str] = []
    partition_definitions: list[dict[str, Any]] = []
    participant_required = frozenset({
        "speaker_aligned_orthographic_transcript",
        "timing_link",
        "dialogue_act",
    })
    observed_selected_classifications: set[str] = set()

    if any(not isinstance(member, dict) for member in members):
        raise ValueError("AMI extraction member evidence must be an object")
    for member in sorted(members, key=lambda item: item.get("path", "")):
        if not isinstance(member, dict):
            raise ValueError("AMI extraction member evidence must be an object")
        member_path = member.get("path")
        classification = member.get("classification")
        selected = member.get("selected")
        if not isinstance(member_path, str) or not isinstance(classification, str):
            raise ValueError("AMI extraction member evidence is invalid")
        if type(selected) is not bool:
            raise ValueError("AMI extraction member selected flag must be boolean")
        classified = classify_ami_member(member_path)
        if (
            classified["classification"] != classification
            or classified["selected"] is not selected
        ):
            raise ValueError(f"AMI member classification drifted: {member_path}")
        if classification == "directory":
            continue

        details: dict[str, Any] = {}
        if selected:
            observed_selected_classifications.add(classification)
            extracted_path = root.joinpath(*member_path.split("/"))
            if not extracted_path.is_file():
                raise ValueError(f"selected AMI annotation file is missing: {member_path}")
            try:
                extracted_path.resolve(strict=True).relative_to(root)
            except ValueError as exc:
                raise ValueError("selected AMI annotation path escaped extraction root") from exc
            selected_paths.append(extracted_path)
            project_relative_path = normalized_relative_path(
                extracted_path,
                inventory_root,
            )
            if extracted_path.suffix.casefold() in {".xml", ".nxt"}:
                file_metadata = _ami_metadata_from_xml(extracted_path)
                for key in source_values:
                    source_values[key].update(file_metadata[key])
                details = {
                    key: sorted(values)
                    for key, values in file_metadata.items()
                }
                if (
                    classification in participant_required
                    and not file_metadata["participants"]
                ):
                    dependency_quarantine.append({
                        "path": project_relative_path,
                        "reason": "required_participant_identity_missing",
                    })
            if classification == "official_partition_metadata":
                partition_paths.append(project_relative_path)
                partition_definition = _ami_partition_definition(
                    extracted_path,
                    project_relative_path=project_relative_path,
                )
                partition_definitions.append(partition_definition)
                details = partition_definition
            disposition = "included"
        else:
            disposition = "excluded"
        quality_items.append({
            "path": member_path,
            "classification": classification,
            "disposition": disposition,
            "reason": member["reason"],
            "selected_file_path": (
                project_relative_path
                if selected
                else None
            ),
            "details": details,
        })

    missing_classifications = (
        AMI_SELECTED_CLASSIFICATIONS - observed_selected_classifications
    )
    if missing_classifications:
        raise ValueError(
            "missing selected AMI material classification: "
            + sorted(missing_classifications)[0]
        )

    _require_complete_ami_partition_definitions(partition_definitions)
    hash_inventory = build_hash_inventory(
        dataset_id=AMI_DATASET_ID,
        project_root=inventory_root,
        selected_paths=selected_paths,
    )
    quality_items.sort(key=lambda item: item["path"])
    dependency_quarantine.sort(key=lambda item: item["path"])
    partition_definitions.sort(
        key=lambda item: (
            item["partition_id"],
            item["source_file_path"],
        )
    )
    included_file_count = sum(
        item["disposition"] == "included"
        for item in quality_items
    )
    excluded_file_count = sum(
        item["disposition"] == "excluded"
        for item in quality_items
    )
    quality_inventory = {
        "quality_inventory_version": 1,
        "dataset_id": AMI_DATASET_ID,
        "included_file_count": included_file_count,
        "excluded_file_count": excluded_file_count,
        "items": quality_items,
        "limitations": [
            "some_tno_participant_metadata_was_not_gathered",
            "documented_synchronization_and_dropout_limitations_exist",
            "media_limitations_are_retained_even_though_media_is_unselected",
        ],
        "dependency_quarantine": dependency_quarantine,
        "source_metadata": {
            "participants": sorted(source_values["participants"]),
            "meetings": sorted(source_values["meetings"]),
            "meeting_series": sorted(source_values["meeting_series"]),
            "recording_sites": sorted(source_values["recording_sites"]),
            "scenarios": sorted(source_values["scenarios"]),
            "source_corpus": AMI_DATASET_ID,
            "multi_party_applicability": True,
            "official_partition_paths": sorted(partition_paths),
            "official_partition_definitions": partition_definitions,
            "official_partition_definitions_are_source_metadata_only": True,
            "project_case_assignments": [],
            "dependency_keys": {
                "speaker": sorted(source_values["participants"]),
                "call_session": sorted(source_values["meetings"]),
                "dialogue_dyad": "not_applicable_multi_party_meeting",
                "source_corpus": [AMI_DATASET_ID],
                "scripted_scenario": sorted(source_values["scenarios"]),
                "meeting_series": sorted(source_values["meeting_series"]),
                "recording_site": sorted(source_values["recording_sites"]),
            },
        },
    }
    return {
        "hash_inventory": hash_inventory,
        "quality_inventory": quality_inventory,
    }


def dataset_profile(dataset_id: str) -> dict[str, Any]:
    if not isinstance(dataset_id, str):
        raise ValueError(f"unknown public dataset: {dataset_id}")
    try:
        profile = _thaw_profile_value(_DATASET_PROFILES[dataset_id])
    except KeyError as exc:
        raise ValueError(f"unknown public dataset: {dataset_id}") from exc
    if not isinstance(profile, dict):
        raise AssertionError("frozen dataset profile did not thaw to an object")
    return profile


def _require_exact_object(value: Any, fields: frozenset[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise PublicDatasetContractError(f"{field} fields mismatch")
    return value


def _require_nonnegative_integer(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise PublicDatasetContractError(f"{field} must be a nonnegative integer")
    return value


def _require_exact_integer(value: Any, expected: int, field: str) -> int:
    if type(value) is not int or value != expected:
        raise PublicDatasetContractError(f"{field} must be integer {expected}")
    return value


def _require_upper_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or UPPER_SHA256_PATTERN.fullmatch(value) is None:
        raise PublicDatasetContractError(f"{field} must be an uppercase SHA-256")
    return value


def _require_access_date(value: Any, *, verified: bool) -> None:
    if value is None:
        if verified:
            raise PublicDatasetContractError("verified manifests require accessed_on")
        return
    if not isinstance(value, str) or ACCESS_DATE_PATTERN.fullmatch(value) is None:
        raise PublicDatasetContractError("accessed_on must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise PublicDatasetContractError("accessed_on must be a real calendar date") from exc
    if parsed.isoformat() != value:
        raise PublicDatasetContractError("accessed_on must use canonical YYYY-MM-DD")


def _validate_manifest_evidence_references(payload: dict[str, Any]) -> None:
    dataset_id = payload["dataset_id"]
    local_hashes = _require_exact_object(
        payload["local_file_hashes"],
        LOCAL_FILE_HASH_FIELDS,
        "local_file_hashes",
    )
    hash_reference = _require_exact_object(
        payload["hash_inventory"],
        HASH_INVENTORY_REFERENCE_FIELDS,
        "hash_inventory",
    )
    exclusion_reference = _require_exact_object(
        payload["exclusion_inventory"],
        EXCLUSION_INVENTORY_FIELDS,
        "exclusion_inventory",
    )
    expected_hash_path = f"research/sources/emotion_state/datasets/{dataset_id}.hashes.json"
    expected_quality_path = f"research/sources/emotion_state/datasets/{dataset_id}.quality.json"
    if local_hashes["algorithm"] != "SHA-256" or hash_reference["algorithm"] != "SHA-256":
        raise PublicDatasetContractError("hash inventory algorithm must be SHA-256")
    if (
        local_hashes["inventory_path"] != expected_hash_path
        or hash_reference["inventory_path"] != expected_hash_path
    ):
        raise PublicDatasetContractError("inventory_path must be the exact project-relative dataset path")
    if hash_reference["schema_id"] != "emotion-state-dataset-hash-inventory-v1":
        raise PublicDatasetContractError("hash_inventory schema_id is invalid")
    _require_exact_integer(hash_reference["schema_version"], 1, "hash_inventory.schema_version")
    if hash_reference["path_normalization"] != "project-relative-posix-nfc":
        raise PublicDatasetContractError("hash_inventory path_normalization is invalid")
    if hash_reference["ordering"] != "ordinal-by-normalized-path":
        raise PublicDatasetContractError("hash_inventory ordering is invalid")
    if exclusion_reference["schema_id"] != "emotion-state-dataset-quality-inventory-reference-v1":
        raise PublicDatasetContractError("exclusion_inventory schema_id is invalid")
    _require_exact_integer(
        exclusion_reference["schema_version"],
        1,
        "exclusion_inventory.schema_version",
    )
    if exclusion_reference["quality_inventory_path"] != expected_quality_path:
        raise PublicDatasetContractError(
            "quality_inventory_path must be the exact project-relative dataset path"
        )
    shared_keys = (
        "algorithm",
        "inventory_path",
        "inventory_sha256",
        "selected_file_count",
        "selected_byte_count",
    )
    if any(local_hashes[key] != hash_reference[key] for key in shared_keys):
        raise PublicDatasetContractError("local_file_hashes is not the exact v1 hash projection")

    if payload["completion_status"] == "material_verification_pending":
        pending_values = (
            local_hashes["inventory_sha256"],
            local_hashes["selected_file_count"],
            local_hashes["selected_byte_count"],
            hash_reference["inventory_sha256"],
            hash_reference["selected_file_count"],
            hash_reference["selected_byte_count"],
            exclusion_reference["quality_inventory_sha256"],
            exclusion_reference["included_file_count"],
            exclusion_reference["excluded_file_count"],
        )
        if any(value is not None for value in pending_values):
            raise PublicDatasetContractError("pending manifests cannot claim hashes or counts")
        return

    _require_upper_sha256(local_hashes["inventory_sha256"], "inventory_sha256")
    _require_upper_sha256(
        exclusion_reference["quality_inventory_sha256"],
        "quality_inventory_sha256",
    )
    selected_file_count = _require_nonnegative_integer(
        local_hashes["selected_file_count"],
        "selected_file_count",
    )
    selected_byte_count = _require_nonnegative_integer(
        local_hashes["selected_byte_count"],
        "selected_byte_count",
    )
    included_file_count = _require_nonnegative_integer(
        exclusion_reference["included_file_count"],
        "included_file_count",
    )
    _require_nonnegative_integer(
        exclusion_reference["excluded_file_count"],
        "excluded_file_count",
    )
    if selected_file_count < 1 or selected_byte_count < 1:
        raise PublicDatasetContractError("verified manifests require positive selected counts")
    if included_file_count < 1:
        raise PublicDatasetContractError("verified manifests require an included quality item")


def validate_dataset_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != REQUIRED_V2_FIELDS:
        raise PublicDatasetContractError("dataset manifest fields mismatch")
    dataset_id = payload["dataset_id"]
    if dataset_id not in SELECTED_PUBLIC_DATASETS:
        raise PublicDatasetContractError("dataset_id is not selected")
    profile = dataset_profile(dataset_id)
    _require_exact_integer(payload["manifest_version"], 2, "manifest_version")
    frozen_manifest_fields = (
        "canonical_source_url",
        "release_or_version",
        "terms_or_license",
        "access_restrictions",
        "source_labels",
        "excluded_labels",
        "language",
        "domain",
        "domain_limitations",
        "permitted_research_lanes",
        "redistribution_status",
        "manifest_version",
        "selected_artifacts",
        "source_revision",
        "release_published_at",
        "dependency_keys",
        "quality_rules",
        "known_issues",
        "runtime_influence_allowed",
    )
    for field in frozen_manifest_fields:
        if payload[field] != profile[field]:
            raise PublicDatasetContractError(f"{field} does not match the frozen dataset profile")
    if payload["source_label"] != "public-only":
        raise PublicDatasetContractError("source_label must be public-only")
    mapping = payload["project_label_mapping"]
    if not isinstance(mapping, dict) or mapping:
        raise PublicDatasetContractError("project_label_mapping must be empty")
    if payload["runtime_influence_allowed"] is not False:
        raise PublicDatasetContractError("public dataset manifests cannot influence runtime")
    completion_status = payload["completion_status"]
    if not isinstance(completion_status, str) or completion_status not in COMPLETION_STATUSES:
        raise PublicDatasetContractError("completion_status is invalid")
    _require_access_date(payload["accessed_on"], verified=completion_status == "verified")
    _validate_manifest_evidence_references(payload)
    return payload


def _normalized_inventory_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise PublicDatasetContractError("inventory file path must be non-empty")
    if "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise PublicDatasetContractError("inventory file path must be project-relative POSIX")
    if unicodedata.normalize("NFC", value) != value:
        raise PublicDatasetContractError("inventory file path must be NFC-normalized")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PublicDatasetContractError("inventory file path contains a dot segment or escape")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value:
        raise PublicDatasetContractError("inventory file path is not canonical")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_hash_inventory(payload: dict[str, Any], dataset_root: Path) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != HASH_INVENTORY_FIELDS:
        raise PublicDatasetContractError("hash inventory fields mismatch")
    _require_exact_integer(payload["inventory_version"], 1, "inventory_version")
    dataset_id = payload["dataset_id"]
    if not isinstance(dataset_id, str) or not dataset_id:
        raise PublicDatasetContractError("dataset_id must be a non-empty string")
    if payload["algorithm"] != "SHA-256":
        raise PublicDatasetContractError("hash inventory algorithm must be SHA-256")
    if payload["path_normalization"] != "project-relative-posix-nfc":
        raise PublicDatasetContractError("hash inventory path_normalization is invalid")
    if payload["ordering"] != "ordinal-by-normalized-path":
        raise PublicDatasetContractError("hash inventory ordering is invalid")
    selected_file_count = _require_nonnegative_integer(
        payload["selected_file_count"],
        "selected_file_count",
    )
    selected_byte_count = _require_nonnegative_integer(
        payload["selected_byte_count"],
        "selected_byte_count",
    )
    files = payload["files"]
    if not isinstance(files, list):
        raise PublicDatasetContractError("files must be a list")
    try:
        root = Path(dataset_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PublicDatasetContractError("dataset_root does not exist") from exc
    if not root.is_dir():
        raise PublicDatasetContractError("dataset_root must be a directory")

    normalized_paths: list[str] = []
    casefold_paths: set[str] = set()
    total_bytes = 0
    for index, entry_value in enumerate(files):
        if not isinstance(entry_value, dict) or set(entry_value) not in {
            HASH_INVENTORY_FILE_FIELDS,
            HASH_INVENTORY_FILE_FIELDS_WITH_LFS,
        }:
            raise PublicDatasetContractError(f"files[{index}] fields mismatch")
        entry = entry_value
        normalized_path = _normalized_inventory_path(entry["path"])
        if normalized_path in normalized_paths:
            raise PublicDatasetContractError("hash inventory contains a duplicate normalized path")
        casefold_path = normalized_path.casefold()
        if casefold_path in casefold_paths:
            raise PublicDatasetContractError("hash inventory contains a case-fold path collision")
        normalized_paths.append(normalized_path)
        casefold_paths.add(casefold_path)
        size_bytes = _require_nonnegative_integer(entry["size_bytes"], "files.size_bytes")
        expected_sha256 = _require_upper_sha256(entry["sha256"], "files.sha256")
        if "git_lfs_oid_sha256" in entry:
            lfs_digest = _require_upper_sha256(
                entry["git_lfs_oid_sha256"],
                "files.git_lfs_oid_sha256",
            )
            if lfs_digest != expected_sha256:
                raise PublicDatasetContractError("Git LFS OID does not match the selected file hash")
        candidate = root.joinpath(*normalized_path.split("/"))
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise PublicDatasetContractError(f"selected inventory file is missing: {normalized_path}") from exc
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise PublicDatasetContractError("selected inventory file escapes dataset_root") from exc
        if not resolved.is_file():
            raise PublicDatasetContractError(f"selected inventory target is not a file: {normalized_path}")
        actual_size = resolved.stat().st_size
        if actual_size != size_bytes:
            raise PublicDatasetContractError(f"selected inventory file size mismatch: {normalized_path}")
        actual_sha256 = _sha256_file(resolved)
        if actual_sha256 != expected_sha256:
            raise PublicDatasetContractError(f"selected inventory file digest mismatch: {normalized_path}")
        total_bytes += actual_size

    if normalized_paths != sorted(normalized_paths):
        raise PublicDatasetContractError("hash inventory files are not in ordinal path order")
    if selected_file_count != len(files):
        raise PublicDatasetContractError("selected_file_count does not match files")
    if selected_byte_count != total_bytes:
        raise PublicDatasetContractError("selected_byte_count does not match files")
    if files:
        if selected_file_count < 1 or selected_byte_count < 1:
            raise PublicDatasetContractError("zero counts are allowed only for an empty inventory")
    elif selected_file_count != 0 or selected_byte_count != 0:
        raise PublicDatasetContractError("empty inventories require zero counts")
    return payload


def _pending_manifest(dataset_id: str) -> dict[str, Any]:
    profile = dataset_profile(dataset_id)
    hash_path = f"research/sources/emotion_state/datasets/{dataset_id}.hashes.json"
    quality_path = f"research/sources/emotion_state/datasets/{dataset_id}.quality.json"
    return {
        "dataset_id": dataset_id,
        "canonical_source_url": profile["canonical_source_url"],
        "release_or_version": profile["release_or_version"],
        "accessed_on": None,
        "terms_or_license": profile["terms_or_license"],
        "access_restrictions": profile["access_restrictions"],
        "local_file_hashes": {
            "algorithm": "SHA-256",
            "inventory_path": hash_path,
            "inventory_sha256": None,
            "selected_file_count": None,
            "selected_byte_count": None,
        },
        "source_label": "public-only",
        "source_labels": profile["source_labels"],
        "project_label_mapping": {},
        "excluded_labels": profile["excluded_labels"],
        "language": profile["language"],
        "domain": profile["domain"],
        "domain_limitations": profile["domain_limitations"],
        "permitted_research_lanes": profile["permitted_research_lanes"],
        "redistribution_status": profile["redistribution_status"],
        "manifest_version": 2,
        "selected_artifacts": profile["selected_artifacts"],
        "source_revision": profile["source_revision"],
        "release_published_at": profile["release_published_at"],
        "dependency_keys": profile["dependency_keys"],
        "quality_rules": profile["quality_rules"],
        "known_issues": profile["known_issues"],
        "exclusion_inventory": {
            "schema_id": "emotion-state-dataset-quality-inventory-reference-v1",
            "schema_version": 1,
            "quality_inventory_path": quality_path,
            "quality_inventory_sha256": None,
            "included_file_count": None,
            "excluded_file_count": None,
        },
        "hash_inventory": {
            "schema_id": "emotion-state-dataset-hash-inventory-v1",
            "schema_version": 1,
            "algorithm": "SHA-256",
            "inventory_path": hash_path,
            "inventory_sha256": None,
            "selected_file_count": None,
            "selected_byte_count": None,
            "path_normalization": "project-relative-posix-nfc",
            "ordering": "ordinal-by-normalized-path",
        },
        "completion_status": "material_verification_pending",
        "runtime_influence_allowed": False,
    }


def public_dataset_contract_self_check() -> str:
    if SELECTED_PUBLIC_DATASETS != (CREMA_DATASET_ID, AMI_DATASET_ID):
        raise AssertionError("selected public dataset order drifted")
    if REQUIRED_V2_FIELDS != REQUIRED_V1_FIELDS | frozenset({
        "manifest_version",
        "selected_artifacts",
        "source_revision",
        "release_published_at",
        "dependency_keys",
        "quality_rules",
        "known_issues",
        "exclusion_inventory",
        "hash_inventory",
        "completion_status",
        "runtime_influence_allowed",
    }):
        raise AssertionError("required dataset manifest fields drifted")
    for dataset_id in SELECTED_PUBLIC_DATASETS:
        profile = dataset_profile(dataset_id)
        if profile["project_label_mapping"] != {}:
            raise AssertionError("public dataset profile claims a project label mapping")
        validate_dataset_manifest(_pending_manifest(dataset_id))
    first = dataset_profile(CREMA_DATASET_ID)
    first["selected_artifacts"].append("mutation")
    if dataset_profile(CREMA_DATASET_ID)["selected_artifacts"] != CREMA_PROFILE_IDENTITY[
        "selected_artifacts"
    ]:
        raise AssertionError("dataset_profile did not return a deep copy")
    return "pass"
