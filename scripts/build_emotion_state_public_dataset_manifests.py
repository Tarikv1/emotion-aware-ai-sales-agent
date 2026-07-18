from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

from scripts.emotion_state_public_dataset_contracts import (
    AMI_DATASET_ID,
    AMI_EXCLUDED_MANUAL_ANNOTATION_FAMILY_CLASSIFICATIONS,
    AMI_EXCLUDED_MANUAL_ANNOTATION_ROOT_FILE_CLASSIFICATIONS,
    AMI_PARTITIONS_SOURCE_RELATIVE_PATH,
    AMI_PARTITIONS_SOURCE_SHA256,
    AMI_PARTITIONS_SOURCE_URL,
    CREMA_AUDIO_PREFIX,
    CREMA_DATASET_ID,
    CREMA_EXCLUDED_PATHS,
    CREMA_KNOWN_NO_AUDIO_FILE,
    CREMA_PROFILE_IDENTITY,
    CREMA_RAW_SOURCE_LABEL_MAP,
    CREMA_SELECTED_FIXED_PATHS,
    SELECTED_PUBLIC_DATASETS,
    _ami_metadata_from_xml,
    _pending_manifest,
    canonical_inventory_bytes,
    classify_ami_member,
    inspect_ami_archive,
    parse_ami_partition_source,
    parse_crema_filename,
    safe_extract_ami_archive,
    validate_ami_material,
    validate_crema_material,
    validate_dataset_manifest,
    validate_hash_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATASET_ROOT = Path("data/public/emotion-state")
OUTPUT_DATASET_ROOT = Path("research/sources/emotion_state/datasets")
QUALITY_ITEM_FIELDS = frozenset({
    "path",
    "classification",
    "disposition",
    "reason",
    "selected_file_path",
    "details",
})
AMI_MANUAL_ANNOTATION_EXCLUSION_CLASSIFICATIONS = (
    frozenset(AMI_EXCLUDED_MANUAL_ANNOTATION_FAMILY_CLASSIFICATIONS.values())
    | frozenset(AMI_EXCLUDED_MANUAL_ANNOTATION_ROOT_FILE_CLASSIFICATIONS.values())
)
CREMA_LIMITATIONS = [
    "raters_heard_audio_presentation_encodings_while_feature_verification_uses_corresponding_wav_files",
    "filename_intended_emotion_is_prompt_metadata_only_and_never_fills_a_missing_perceived_label",
    "filename_agreement_cannot_override_an_official_mismatch_or_objective_content_or_duration_failure",
]
AMI_LIMITATIONS = [
    "some_tno_participant_metadata_was_not_gathered",
    "documented_synchronization_and_dropout_limitations_exist",
    "media_limitations_are_retained_even_though_media_is_unselected",
]
GIT_COMMAND_TIMEOUT_SECONDS = 20.0
GitCommand = Callable[..., bytes]


def _argument_path(value: str | Path, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _guard_public_path(
    value: str | Path,
    *,
    project_root: Path,
    field: str,
    must_exist: bool,
    must_be_directory: bool | None = None,
) -> Path:
    candidate = _argument_path(value, project_root)
    resolved_project_root = project_root.resolve(strict=True)
    private_roots = (
        (resolved_project_root / "data" / "private").resolve(strict=False),
        (resolved_project_root / "data" / "private-restricted").resolve(strict=False),
    )
    unresolved = candidate.resolve(strict=False)
    if any(_is_relative_to(unresolved, private_root) for private_root in private_roots):
        raise ValueError(f"{field} rejects private dataset paths")
    public_root = (resolved_project_root / PUBLIC_DATASET_ROOT).resolve(strict=False)
    if not _is_relative_to(unresolved, public_root):
        raise ValueError(f"{field} must remain under data/public/emotion-state/")
    if must_exist:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"{field} does not exist") from exc
        if not _is_relative_to(resolved, public_root):
            raise ValueError(f"{field} resolves outside data/public/emotion-state/")
    else:
        resolved = unresolved
    if must_be_directory is True and not resolved.is_dir():
        raise ValueError(f"{field} must be a directory")
    if must_be_directory is False and not resolved.is_file():
        raise ValueError(f"{field} must be a file")
    if must_be_directory is None and resolved.exists() and not resolved.is_dir():
        raise ValueError(f"{field} must be a directory when it already exists")
    return resolved


def _guard_output_root(value: str | Path, project_root: Path) -> Path:
    resolved_project_root = project_root.resolve(strict=True)
    candidate = _argument_path(value, resolved_project_root).resolve(strict=False)
    expected = (resolved_project_root / OUTPUT_DATASET_ROOT).resolve(strict=False)
    if candidate != expected:
        raise ValueError(
            "output root must be research/sources/emotion_state/datasets/"
        )
    return candidate


def _canonical_access_date(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("accessed-on must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("accessed-on must be a real YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise ValueError("accessed-on must use canonical YYYY-MM-DD")
    return value


def _run_git_command(
    argv: list[str],
    *,
    cwd: Path,
    timeout_seconds: float,
) -> bytes:
    if (
        not argv
        or argv[0] != "git"
        or type(timeout_seconds) not in {int, float}
        or timeout_seconds <= 0
        or timeout_seconds > 60
    ):
        raise ValueError("local Git command boundary is invalid")
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError("local Git executable is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("local Git metadata command timed out") from exc
    if completed.returncode != 0:
        error = completed.stderr.decode("utf-8", errors="replace").strip()
        if len(error) > 512:
            error = error[:512]
        raise ValueError(f"local Git metadata command failed: {error}")
    return completed.stdout


def parse_git_lfs_pointer(payload: bytes, *, path: str) -> str:
    if not isinstance(payload, bytes):
        raise ValueError(f"Git LFS pointer payload is invalid: {path}")
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ValueError(f"Git LFS pointer is not UTF-8: {path}") from exc
    if len(lines) != 3:
        raise ValueError(f"Git LFS pointer fields mismatch: {path}")
    if lines[0] != "version https://git-lfs.github.com/spec/v1":
        raise ValueError(f"Git LFS pointer version is invalid: {path}")
    oid_match = re.fullmatch(r"oid sha256:([0-9A-Fa-f]{64})", lines[1])
    size_match = re.fullmatch(r"size (0|[1-9]\d*)", lines[2])
    if oid_match is None or size_match is None:
        raise ValueError(f"Git LFS pointer metadata is malformed: {path}")
    return oid_match.group(1).upper()


def discover_crema_lfs_oids(
    crema_root: Path,
    *,
    project_root: Path,
    expected_revision: str = CREMA_PROFILE_IDENTITY["source_revision"],
    git_command: GitCommand = _run_git_command,
) -> dict[Path, str]:
    try:
        repository_root = Path(crema_root).resolve(strict=True)
        approved_project_root = Path(project_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("CREMA-D local Git repository is missing") from exc
    if not repository_root.is_dir():
        raise ValueError("CREMA-D local Git repository must be a directory")
    try:
        repository_root.relative_to(approved_project_root)
    except ValueError as exc:
        raise ValueError("CREMA-D local Git repository escapes the project root") from exc
    if re.fullmatch(r"[0-9A-Fa-f]{40}", expected_revision) is None:
        raise ValueError("frozen CREMA-D source revision is invalid")

    base_argv = ["git", "-C", str(repository_root)]
    top_level_bytes = git_command(
        [*base_argv, "rev-parse", "--show-toplevel"],
        cwd=approved_project_root,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    )
    try:
        top_level = Path(top_level_bytes.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, RuntimeError, UnicodeError) as exc:
        raise ValueError("CREMA-D Git top-level metadata is invalid") from exc
    if top_level != repository_root:
        raise ValueError("CREMA-D root is not the exact local Git repository top-level")

    head = git_command(
        [*base_argv, "rev-parse", "HEAD"],
        cwd=approved_project_root,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[0-9A-Fa-f]{40}", head) is None:
        raise ValueError("CREMA-D Git HEAD metadata is invalid")
    if head.casefold() != expected_revision.casefold():
        raise ValueError("CREMA-D Git HEAD does not match the frozen source revision")

    archive_bytes = git_command(
        [
            *base_argv,
            "archive",
            "--format=tar",
            "HEAD",
            "--",
            "AudioWAV",
        ],
        cwd=approved_project_root,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    )
    pointer_oids: dict[str, str] = {}
    casefold_paths: set[str] = set()
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
            for member in sorted(archive.getmembers(), key=lambda item: item.name):
                if member.isdir():
                    continue
                normalized_path = unicodedata.normalize(
                    "NFC",
                    member.name.replace("\\", "/"),
                )
                parts = normalized_path.split("/")
                if (
                    not member.isfile()
                    or len(parts) < 2
                    or parts[0] != "AudioWAV"
                    or any(part in {"", ".", ".."} for part in parts)
                ):
                    raise ValueError("CREMA-D Git archive path is invalid")
                if not normalized_path.casefold().endswith(".wav"):
                    continue
                if normalized_path in pointer_oids:
                    raise ValueError("duplicate CREMA-D Git LFS pointer path")
                casefold_path = normalized_path.casefold()
                if casefold_path in casefold_paths:
                    raise ValueError("case-fold CREMA-D Git LFS pointer collision")
                if member.size > 4096:
                    raise ValueError(
                        f"Git LFS pointer is unexpectedly large: {normalized_path}"
                    )
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(
                        f"Git LFS pointer is unreadable: {normalized_path}"
                    )
                pointer_oids[normalized_path] = parse_git_lfs_pointer(
                    source.read(),
                    path=normalized_path,
                )
                casefold_paths.add(casefold_path)
    except tarfile.TarError as exc:
        raise ValueError("CREMA-D Git archive metadata is unreadable") from exc

    selected_working_paths = {
        path.relative_to(repository_root).as_posix(): path.resolve(strict=True)
        for path in sorted((repository_root / "AudioWAV").rglob("*.wav"))
        if path.is_file()
        and path.relative_to(repository_root).as_posix()
        != CREMA_KNOWN_NO_AUDIO_FILE
    }
    selected_pointer_oids = {
        path: oid
        for path, oid in pointer_oids.items()
        if path != CREMA_KNOWN_NO_AUDIO_FILE
    }
    missing = set(selected_working_paths) - set(selected_pointer_oids)
    if missing:
        raise ValueError(
            "missing selected CREMA-D Git LFS pointer metadata: "
            + sorted(missing)[0]
        )
    unbound = set(selected_pointer_oids) - set(selected_working_paths)
    if unbound:
        raise ValueError(
            "unbound CREMA-D Git LFS pointer metadata: "
            + sorted(unbound)[0]
        )
    return {
        selected_working_paths[path]: selected_pointer_oids[path]
        for path in sorted(selected_working_paths)
    }


def _require_exact_dict(
    value: Any,
    fields: frozenset[str],
    field: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"quality inventory {field} fields mismatch")
    return value


def _require_quality_string(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or "\n" in value
        or "\r" in value
        or "\x00" in value
    ):
        raise ValueError(f"quality inventory {field} must be a bounded single-line string")
    return value


def _require_quality_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"quality inventory {field} must be a list")
    values = [
        _require_quality_string(item, f"{field}[]")
        for item in value
    ]
    if values != sorted(values) or len(values) != len(set(values)):
        raise ValueError(f"quality inventory {field} must be sorted and unique")
    return values


def _require_canonical_quality_path(value: Any, field: str) -> str:
    path = _require_quality_string(value, field)
    if (
        path.startswith("/")
        or re.match(r"^[A-Za-z]:", path) is not None
        or "\\" in path
        or ":" in path
        or any(character.isspace() for character in path)
    ):
        raise ValueError(
            f"quality inventory {field} must be a canonical relative path"
        )
    if unicodedata.normalize("NFC", path) != path:
        raise ValueError(
            f"quality inventory {field} must be a canonical relative path"
        )
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(
            f"quality inventory {field} must be a canonical relative path"
        )
    pure = PurePosixPath(path)
    if pure.is_absolute() or pure.as_posix() != path:
        raise ValueError(
            f"quality inventory {field} must be a canonical relative path"
        )
    return path


def _require_canonical_quality_path_list(value: Any, field: str) -> list[str]:
    paths = _require_quality_string_list(value, field)
    for index, path in enumerate(paths):
        _require_canonical_quality_path(path, f"{field}[{index}]")
    return paths


def _require_crema_audio_wav_path(value: Any, field: str) -> str:
    path = _require_canonical_quality_path(value, field)
    if not path.startswith(CREMA_AUDIO_PREFIX):
        raise ValueError(f"quality inventory {field} is outside AudioWAV/")
    filename = path.removeprefix(CREMA_AUDIO_PREFIX)
    if not filename or "/" in filename or not filename.casefold().endswith(".wav"):
        raise ValueError(f"quality inventory {field} is not a CREMA WAV path")
    try:
        parse_crema_filename(filename)
    except ValueError as exc:
        raise ValueError(
            f"quality inventory {field} is not a CREMA WAV path"
        ) from exc
    return path


def _require_crema_item_path(
    value: Any,
    *,
    classification: str,
    field: str,
) -> str:
    path = _require_canonical_quality_path(value, field)
    if classification == "crema_pcm_wav":
        _require_crema_audio_wav_path(path, field)
        if path == CREMA_KNOWN_NO_AUDIO_FILE:
            raise ValueError("quality inventory CREMA known issue path is misclassified")
    elif classification == "crema_wav":
        if path != CREMA_KNOWN_NO_AUDIO_FILE:
            raise ValueError("quality inventory CREMA known issue path is invalid")
    elif classification == "crema_audio_directory_non_wav":
        if (
            not path.startswith(CREMA_AUDIO_PREFIX)
            or path.removeprefix(CREMA_AUDIO_PREFIX) == ""
            or path.casefold().endswith(".wav")
        ):
            raise ValueError("quality inventory CREMA non-WAV path is invalid")
    elif classification == "crema_release_metadata":
        if path not in CREMA_SELECTED_FIXED_PATHS:
            raise ValueError("quality inventory CREMA fixed metadata path is invalid")
    elif classification == "crema_demographic_metadata":
        if path not in CREMA_EXCLUDED_PATHS:
            raise ValueError("quality inventory CREMA demographic path is invalid")
    elif classification == "crema_unselected_release_material":
        if (
            path in CREMA_SELECTED_FIXED_PATHS
            or path in CREMA_EXCLUDED_PATHS
            or path.startswith(CREMA_AUDIO_PREFIX)
        ):
            raise ValueError("quality inventory CREMA exclusion path is invalid")
    else:
        raise ValueError("quality inventory CREMA classification is invalid")
    return path


def _require_ami_item_path(
    value: Any,
    *,
    classification: str,
    disposition: str,
    field: str,
) -> str:
    path = _require_canonical_quality_path(value, field)
    if classification == "downloaded_archive":
        if not path.casefold().endswith(".zip"):
            raise ValueError("quality inventory AMI archive path is invalid")
        return path
    if classification == "official_partition_metadata":
        if path != AMI_PARTITIONS_SOURCE_RELATIVE_PATH:
            raise ValueError("quality inventory AMI partition source path is invalid")
        return path
    classified = classify_ami_member(path)
    if (
        classified["classification"] != classification
        or classified["selected"] is not (disposition == "included")
    ):
        raise ValueError("quality inventory AMI item path classification mismatch")
    return path


def _require_selected_path_binding(
    value: Any,
    *,
    item_path: str,
    classification: str,
    field: str,
) -> str:
    selected_path = _require_canonical_quality_path(value, field)
    if classification == "downloaded_archive":
        bound = selected_path == item_path
    else:
        bound = (
            selected_path == item_path
            or selected_path.endswith("/" + item_path)
        )
    if not bound:
        raise ValueError(
            "quality inventory selected file set item binding mismatch: "
            f"{field}"
        )
    return selected_path


def _require_quality_identifier(value: Any, field: str) -> str:
    identifier = _require_quality_string(value, field)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", identifier) is None:
        raise ValueError(f"quality inventory {field} must be an identifier")
    return identifier


def _require_quality_identifier_list(value: Any, field: str) -> list[str]:
    values = _require_quality_string_list(value, field)
    for index, item in enumerate(values):
        _require_quality_identifier(item, f"{field}[{index}]")
    return values


def _reject_forbidden_quality_payload_keys(value: Any, field: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"quality inventory {field} keys must be strings")
            normalized = re.sub(r"[^a-z0-9]+", "_", key.casefold()).strip("_")
            if (
                normalized in {
                    "body",
                    "content",
                    "raw_text",
                    "raw_transcript",
                    "text",
                    "transcript",
                    "transcript_body",
                    "transcript_text",
                    "utterance_text",
                }
                or normalized.endswith(("_body", "_content", "_raw_transcript", "_text"))
            ):
                raise ValueError(
                    f"quality inventory contains forbidden raw-text field: {field}.{key}"
                )
            _reject_forbidden_quality_payload_keys(item, f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_forbidden_quality_payload_keys(item, f"{field}[{index}]")


def _validate_crema_filename_metadata(value: Any) -> dict[str, Any]:
    filename = _require_exact_dict(
        value,
        frozenset({
            "actor_id",
            "sentence_code",
            "intended_emotion_code",
            "intensity_code",
            "extension",
            "intended_source_label",
            "intended_label_role",
        }),
        "CREMA filename_metadata",
    )
    for key in (
        "actor_id",
        "sentence_code",
        "intended_emotion_code",
        "intensity_code",
        "extension",
        "intended_source_label",
        "intended_label_role",
    ):
        _require_quality_identifier(
            filename[key],
            f"CREMA filename_metadata.{key}",
        )
    if (
        filename["extension"] != "wav"
        or filename["intended_label_role"] != "prompt_metadata_only"
    ):
        raise ValueError("quality inventory CREMA filename metadata is invalid")
    return filename


def _validate_crema_quality_item(item: dict[str, Any]) -> None:
    classification = item["classification"]
    disposition = item["disposition"]
    reason = item["reason"]
    details = item["details"]
    if classification == "crema_pcm_wav":
        if disposition != "included" or reason not in {
            "frozen_audio_wav_selection",
            "official_mismatch_wav_counterpart_objectively_validated",
        }:
            raise ValueError("quality inventory CREMA WAV disposition/reason mismatch")
        details = _require_exact_dict(
            details,
            frozenset({
                "filename_metadata",
                "wav_metadata",
                "source_label_evidence",
                "dependency_keys",
            }),
            "CREMA WAV details",
        )
        _validate_crema_filename_metadata(details["filename_metadata"])
        wav = _require_exact_dict(
            details["wav_metadata"],
            frozenset({
                "channel_count",
                "sample_width_bytes",
                "sample_rate_hz",
                "frame_count",
                "duration_seconds",
                "encoding",
            }),
            "CREMA wav_metadata",
        )
        for key in ("channel_count", "sample_width_bytes", "sample_rate_hz", "frame_count"):
            if type(wav[key]) is not int or wav[key] <= 0:
                raise ValueError(f"quality inventory CREMA wav_metadata.{key} is invalid")
        if (
            type(wav["duration_seconds"]) not in {int, float}
            or wav["duration_seconds"] <= 0
            or wav["encoding"] != "PCM"
        ):
            raise ValueError("quality inventory CREMA WAV duration/encoding is invalid")
        source = _require_exact_dict(
            details["source_label_evidence"],
            frozenset({
                "raw_source_label",
                "normalized_source_label",
                "source_column",
                "vote_distribution",
                "agreement",
                "ambiguous",
                "abstained",
                "ambiguity_reason",
                "audio_presentation_encodings",
                "source_file_path",
            }),
            "CREMA source_label_evidence",
        )
        raw_label = source["raw_source_label"]
        normalized_label = source["normalized_source_label"]
        if raw_label is not None:
            if raw_label not in CREMA_RAW_SOURCE_LABEL_MAP:
                raise ValueError("quality inventory CREMA raw source label is invalid")
            if normalized_label != CREMA_RAW_SOURCE_LABEL_MAP[raw_label]:
                raise ValueError("quality inventory CREMA normalized source label is invalid")
        elif normalized_label is not None:
            raise ValueError("quality inventory CREMA missing raw label cannot be normalized")
        if type(source["ambiguous"]) is not bool or type(source["abstained"]) is not bool:
            raise ValueError("quality inventory CREMA ambiguity flags must be booleans")
        source_column = source["source_column"]
        if isinstance(source_column, str):
            _require_quality_identifier(source_column, "CREMA source_column")
        elif isinstance(source_column, list):
            _require_quality_identifier_list(source_column, "CREMA source_column")
        elif source_column is not None:
            raise ValueError("quality inventory CREMA source_column is invalid")
        agreement = source["agreement"]
        if agreement is not None and (
            type(agreement) not in {int, float}
            or agreement < 0
            or agreement > 1
        ):
            raise ValueError("quality inventory CREMA agreement is invalid")
        if source["ambiguity_reason"] not in {
            None,
            "tied_audio_only_majority_labels",
            "missing_audio_only_perceived_label",
        }:
            raise ValueError("quality inventory CREMA ambiguity reason is invalid")
        source_file_path = _require_canonical_quality_path(
            source["source_file_path"],
            "CREMA source_file_path",
        )
        if source_file_path != "finishedResponses.csv":
            raise ValueError("quality inventory CREMA source file path is invalid")
        vote_distribution = source["vote_distribution"]
        if not isinstance(vote_distribution, dict):
            raise ValueError("quality inventory CREMA vote_distribution must be an object")
        for code, count in vote_distribution.items():
            if code not in CREMA_RAW_SOURCE_LABEL_MAP or type(count) is not int or count <= 0:
                raise ValueError("quality inventory CREMA vote_distribution is invalid")
        _require_quality_identifier_list(
            source["audio_presentation_encodings"],
            "CREMA audio_presentation_encodings",
        )
        dependency_keys = _require_exact_dict(
            details["dependency_keys"],
            frozenset({"speaker", "source_corpus", "scripted_scenario"}),
            "CREMA dependency_keys",
        )
        if dependency_keys["source_corpus"] != CREMA_DATASET_ID:
            raise ValueError("quality inventory CREMA source_corpus is invalid")
        _require_quality_identifier(
            dependency_keys["speaker"],
            "CREMA dependency speaker",
        )
        _require_quality_identifier(
            dependency_keys["scripted_scenario"],
            "CREMA dependency scenario",
        )
        return
    if classification == "crema_release_metadata":
        if disposition != "included" or reason != "frozen_fixed_selection" or details != {}:
            raise ValueError("quality inventory CREMA fixed metadata item is invalid")
        return
    if classification == "crema_wav":
        if (
            disposition != "excluded"
            or reason != "official_known_no_audio_issue"
        ):
            raise ValueError("quality inventory CREMA known issue item is invalid")
        known = _require_exact_dict(
            details,
            frozenset({
                "filename_metadata",
                "official_issue",
                "objective_failure_confirmed",
                "objective_failure",
            }),
            "CREMA known issue details",
        )
        if known["objective_failure_confirmed"] is not True:
            raise ValueError("quality inventory CREMA known issue is unconfirmed")
        _validate_crema_filename_metadata(known["filename_metadata"])
        if (
            known["official_issue"]
            != "1076_MTI_SAD_XX.wav_has_an_official_documented_no_audio_issue"
            or known["objective_failure"] != "objective_wav_validation_failed"
        ):
            raise ValueError("quality inventory CREMA known issue evidence is invalid")
        return
    allowed_exclusions = {
        "crema_audio_directory_non_wav": "frozen_selection_requires_wav",
        "crema_demographic_metadata": "excluded_demographic_metadata",
        "crema_unselected_release_material": "outside_frozen_selection",
    }
    if (
        disposition != "excluded"
        or allowed_exclusions.get(classification) != reason
        or details != {}
    ):
        raise ValueError("quality inventory CREMA exclusion item is invalid")


def _validate_ami_quality_item(item: dict[str, Any]) -> None:
    classification = item["classification"]
    disposition = item["disposition"]
    reason = item["reason"]
    details = item["details"]
    if classification == "downloaded_archive":
        archive = _require_exact_dict(
            details,
            frozenset({"archive_sha256", "archive_size_bytes"}),
            "AMI archive details",
        )
        if (
            disposition != "included"
            or reason != "archive_hashed_before_extraction"
            or not isinstance(archive["archive_sha256"], str)
            or re.fullmatch(r"[0-9A-F]{64}", archive["archive_sha256"]) is None
            or type(archive["archive_size_bytes"]) is not int
            or archive["archive_size_bytes"] <= 0
        ):
            raise ValueError("quality inventory AMI archive item is invalid")
        return
    if classification in {
        "manual_nxt_metadata",
        "speaker_aligned_orthographic_transcript",
        "timing_link",
        "dialogue_act",
    }:
        metadata = _require_exact_dict(
            details,
            frozenset({
                "participants",
                "meetings",
                "meeting_series",
                "recording_sites",
                "scenarios",
            }),
            "AMI selected XML details",
        )
        if disposition != "included" or reason != "selected_manual_annotation_material":
            raise ValueError("quality inventory AMI selected XML item is invalid")
        for key, value in metadata.items():
            _require_quality_identifier_list(value, f"AMI selected XML {key}")
        return
    if classification == "official_partition_metadata":
        source = _require_exact_dict(
            details,
            frozenset({
                "canonical_source_url",
                "source_file_path",
                "source_sha256",
                "meeting_universe_source_file_path",
                "partition_definitions",
            }),
            "AMI partition source details",
        )
        if disposition != "included" or reason != "selected_official_partition_source":
            raise ValueError("quality inventory AMI partition item is invalid")
        source_file_path = _require_canonical_quality_path(
            source["source_file_path"],
            "AMI partition source_file_path",
        )
        if source_file_path != item["selected_file_path"]:
            raise ValueError(
                "quality inventory AMI partition source path is not selected"
            )
        if re.fullmatch(r"[0-9A-F]{64}", source["source_sha256"]) is None:
            raise ValueError("quality inventory AMI partition source hash is invalid")
        _require_complete_ami_quality_partition_definitions(
            source["partition_definitions"],
            "AMI partition source definitions",
        )
        return
    allowed_exclusions = {
        "audio",
        "video",
        "automatic_annotation",
        "dome",
        "social_role",
        "speculative_emotion",
        "documentation",
        "unselected_release_material",
    } | AMI_MANUAL_ANNOTATION_EXCLUSION_CLASSIFICATIONS
    if (
        classification not in allowed_exclusions
        or disposition != "excluded"
        or reason != f"excluded_{classification}"
        or details != {}
    ):
        raise ValueError("quality inventory AMI exclusion item is invalid")


def _require_complete_ami_quality_partition_definitions(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"quality inventory {field} must be a list")
    definitions: list[dict[str, Any]] = []
    normalized_definitions: list[tuple[str, str]] = []
    signatures: list[tuple[str, str, str, tuple[str, ...]]] = []
    for index, definition_value in enumerate(value):
        definition = _require_exact_dict(
            definition_value,
            frozenset({
                "partition_id",
                "partition_type",
                "source_file_path",
                "meeting_ids",
            }),
            f"{field}[{index}]",
        )
        partition_id = _require_quality_identifier(
            definition["partition_id"],
            f"{field}[{index}].partition_id",
        )
        partition_type = definition["partition_type"]
        if partition_type not in {"scenario", "full_corpus"}:
            raise ValueError("quality inventory AMI partition type is invalid")
        source_file_path = _require_canonical_quality_path(
            definition["source_file_path"],
            f"{field}[{index}].source_file_path",
        )
        meeting_ids = _require_quality_identifier_list(
            definition["meeting_ids"],
            f"{field}[{index}].meeting_ids",
        )
        definitions.append(definition)
        normalized_definitions.append((partition_id, source_file_path))
        signatures.append(
            (
                partition_id,
                partition_type,
                source_file_path,
                tuple(meeting_ids),
            )
        )
    if len(signatures) != len(set(signatures)):
        raise ValueError("quality inventory contains a duplicate AMI partition definition")
    partition_ids = [signature[0] for signature in signatures]
    if len(partition_ids) != len(set(partition_ids)):
        raise ValueError("quality inventory contains a duplicate AMI partition ID")
    partition_types = {signature[1] for signature in signatures}
    if partition_types != {"scenario", "full_corpus"}:
        raise ValueError(
            "quality inventory AMI partition types must be exactly "
            "scenario and full_corpus"
        )
    if {signature[0] for signature in signatures} != {"scenario-only", "full-corpus"}:
        raise ValueError("quality inventory AMI partition IDs are invalid")
    if normalized_definitions != sorted(normalized_definitions):
        raise ValueError("quality inventory AMI partition definitions must be sorted")
    return definitions


def _validate_quality_source_metadata(
    payload: dict[str, Any],
    dataset_id: str,
    *,
    item_paths: set[str],
    ami_partition_definitions: list[dict[str, Any]],
) -> None:
    if dataset_id == CREMA_DATASET_ID:
        metadata = _require_exact_dict(
            payload,
            frozenset({
                "official_mismatch_wav_counterparts",
                "advertised_utterance_count_used",
                "selected_encoding",
                "source_label_rows",
            }),
            "CREMA source_metadata",
        )
        mismatch_paths = _require_canonical_quality_path_list(
            metadata["official_mismatch_wav_counterparts"],
            "CREMA official mismatch counterparts",
        )
        for index, path in enumerate(mismatch_paths):
            _require_crema_audio_wav_path(
                path,
                f"CREMA official mismatch counterparts[{index}]",
            )
        if not set(mismatch_paths).issubset(item_paths):
            raise ValueError(
                "quality inventory CREMA mismatch paths are not quality items"
            )
        if (
            metadata["advertised_utterance_count_used"] is not False
            or metadata["selected_encoding"] != "wav"
            or metadata["source_label_rows"]
            != "finishedResponses.csv audio-only rows"
        ):
            raise ValueError("quality inventory CREMA source_metadata is invalid")
        return
    metadata = _require_exact_dict(
        payload,
        frozenset({
            "participants",
            "meetings",
            "meeting_series",
            "recording_sites",
            "scenarios",
            "source_corpus",
            "multi_party_applicability",
            "official_partition_paths",
            "official_partition_source",
            "official_partition_definitions",
            "official_partition_definitions_are_source_metadata_only",
            "project_case_assignments",
            "dependency_keys",
        }),
        "AMI source_metadata",
    )
    for key in (
        "participants",
        "meetings",
        "meeting_series",
        "recording_sites",
        "scenarios",
    ):
        _require_quality_identifier_list(
            metadata[key],
            f"AMI source_metadata.{key}",
        )
    partition_paths = _require_canonical_quality_path_list(
        metadata["official_partition_paths"],
        "AMI source_metadata.official_partition_paths",
    )
    definitions = _require_complete_ami_quality_partition_definitions(
        metadata["official_partition_definitions"],
        "AMI official_partition_definitions",
    )
    definition_paths = [
        definition["source_file_path"]
        for definition in definitions
    ]
    if partition_paths != [metadata["official_partition_source"]["source_file_path"]]:
        raise ValueError("quality inventory AMI partition paths mismatch definitions")
    if definitions != ami_partition_definitions:
        raise ValueError(
            "quality inventory AMI partition definitions mismatch quality items"
        )
    if (
        metadata["source_corpus"] != AMI_DATASET_ID
        or metadata["multi_party_applicability"] is not True
        or metadata["official_partition_definitions_are_source_metadata_only"]
        is not True
        or metadata["project_case_assignments"] != []
    ):
        raise ValueError("quality inventory AMI source_metadata is invalid")
    dependency_keys = _require_exact_dict(
        metadata["dependency_keys"],
        frozenset({
            "speaker",
            "call_session",
            "dialogue_dyad",
            "source_corpus",
            "scripted_scenario",
            "meeting_series",
            "recording_site",
        }),
        "AMI dependency_keys",
    )
    for key in (
        "speaker",
        "call_session",
        "source_corpus",
        "scripted_scenario",
        "meeting_series",
        "recording_site",
    ):
        _require_quality_identifier_list(
            dependency_keys[key],
            f"AMI dependency_keys.{key}",
        )
    if dependency_keys["dialogue_dyad"] != "not_applicable_multi_party_meeting":
        raise ValueError("quality inventory AMI dialogue_dyad is invalid")


def _validate_quality_inventory(
    payload: Any,
    *,
    dataset_id: str,
    selected_file_paths: set[str],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("quality inventory must be an object")
    _reject_forbidden_quality_payload_keys(payload, "root")
    required = {
        "quality_inventory_version",
        "dataset_id",
        "included_file_count",
        "excluded_file_count",
        "items",
        "limitations",
        "dependency_quarantine",
        "source_metadata",
    }
    if set(payload) != required:
        raise ValueError("quality inventory fields mismatch")
    if type(payload["quality_inventory_version"]) is not int:
        raise ValueError("quality inventory version must be integer 1")
    if payload["quality_inventory_version"] != 1:
        raise ValueError("quality inventory version must be integer 1")
    if payload["dataset_id"] != dataset_id:
        raise ValueError("quality inventory dataset_id mismatch")
    if type(payload["included_file_count"]) is not int:
        raise ValueError("quality inventory included_file_count must be an integer")
    if type(payload["excluded_file_count"]) is not int:
        raise ValueError("quality inventory excluded_file_count must be an integer")
    items = payload["items"]
    if not isinstance(items, list):
        raise ValueError("quality inventory items must be a list")
    dispositions: list[str] = []
    item_paths: list[str] = []
    included_paths: list[str] = []
    ami_partition_definitions: list[dict[str, Any]] = []
    ami_quarantine_eligible_paths: set[str] = set()
    for index, item_value in enumerate(items):
        item = _require_exact_dict(
            item_value,
            QUALITY_ITEM_FIELDS,
            f"items[{index}]",
        )
        classification = _require_quality_string(
            item["classification"],
            f"items[{index}].classification",
        )
        disposition = item["disposition"]
        if disposition not in {"included", "excluded"}:
            raise ValueError("quality inventory disposition is invalid")
        if dataset_id == CREMA_DATASET_ID:
            path = _require_crema_item_path(
                item["path"],
                classification=classification,
                field=f"items[{index}].path",
            )
        elif dataset_id == AMI_DATASET_ID:
            path = _require_ami_item_path(
                item["path"],
                classification=classification,
                disposition=disposition,
                field=f"items[{index}].path",
            )
        else:
            raise ValueError("quality inventory dataset_id is not selected")
        _require_quality_string(item["reason"], f"items[{index}].reason")
        if not isinstance(item["details"], dict):
            raise ValueError("quality inventory details must be an object")
        selected_file_path = item["selected_file_path"]
        if disposition == "included":
            selected_file_path = _require_selected_path_binding(
                selected_file_path,
                item_path=path,
                classification=classification,
                field=f"items[{index}].selected_file_path",
            )
            included_paths.append(selected_file_path)
        elif selected_file_path is not None:
            raise ValueError("quality inventory excluded item selects a file")
        if dataset_id == CREMA_DATASET_ID:
            _validate_crema_quality_item(item)
        else:
            _validate_ami_quality_item(item)
            if classification == "official_partition_metadata":
                ami_partition_definitions.extend(item["details"]["partition_definitions"])
            if classification in {
                "speaker_aligned_orthographic_transcript",
                "timing_link",
                "dialogue_act",
            }:
                ami_quarantine_eligible_paths.add(selected_file_path)
        dispositions.append(disposition)
        item_paths.append(path)
        if not classification:
            raise AssertionError("validated classification became empty")
    if item_paths != sorted(item_paths) or len(item_paths) != len(set(item_paths)):
        raise ValueError("quality inventory item paths must be sorted and unique")
    if len(included_paths) != len(set(included_paths)):
        raise ValueError("quality inventory selected file paths must be unique")
    if set(included_paths) != selected_file_paths:
        raise ValueError("quality inventory selected file set mismatch")
    if dataset_id == AMI_DATASET_ID:
        ami_partition_definitions = (
            _require_complete_ami_quality_partition_definitions(
                ami_partition_definitions,
                "AMI partition quality items",
            )
        )
    included = sum(value == "included" for value in dispositions)
    excluded = sum(value == "excluded" for value in dispositions)
    if included != payload["included_file_count"]:
        raise ValueError("quality inventory included_file_count mismatch")
    if excluded != payload["excluded_file_count"]:
        raise ValueError("quality inventory excluded_file_count mismatch")
    limitations = (
        CREMA_LIMITATIONS
        if dataset_id == CREMA_DATASET_ID
        else AMI_LIMITATIONS
    )
    if payload["limitations"] != limitations:
        raise ValueError("quality inventory limitations mismatch")
    quarantine = payload["dependency_quarantine"]
    if dataset_id == CREMA_DATASET_ID:
        if quarantine != []:
            raise ValueError("quality inventory CREMA quarantine must be empty")
    else:
        if not isinstance(quarantine, list):
            raise ValueError("quality inventory AMI quarantine must be a list")
        quarantine_paths: list[str] = []
        for index, entry_value in enumerate(quarantine):
            entry = _require_exact_dict(
                entry_value,
                frozenset({"path", "reason"}),
                f"dependency_quarantine[{index}]",
            )
            quarantine_paths.append(
                _require_canonical_quality_path(
                    entry["path"],
                    f"dependency_quarantine[{index}].path",
                )
            )
            if entry["reason"] != "required_participant_identity_missing":
                raise ValueError("quality inventory AMI quarantine reason is invalid")
        if (
            quarantine_paths != sorted(quarantine_paths)
            or len(quarantine_paths) != len(set(quarantine_paths))
        ):
            raise ValueError("quality inventory AMI quarantine must be sorted and unique")
        if not set(quarantine_paths).issubset(ami_quarantine_eligible_paths):
            raise ValueError(
                "quality inventory AMI quarantine path is not a selected participant item"
            )
    _validate_quality_source_metadata(
        payload["source_metadata"],
        dataset_id,
        item_paths=set(item_paths),
        ami_partition_definitions=ami_partition_definitions,
    )
    return payload


def _validate_ami_partition_source_bindings(
    quality_inventory: dict[str, Any],
    *,
    selected_file_paths: set[str],
    project_root: Path,
) -> None:
    metadata = quality_inventory["source_metadata"]
    partition_items = [
        item for item in quality_inventory["items"]
        if item["classification"] == "official_partition_metadata"
    ]
    if len(partition_items) != 1:
        raise ValueError("AMI partition source requires exactly one quality item")
    source = partition_items[0]["details"]
    if (
        source["canonical_source_url"] != AMI_PARTITIONS_SOURCE_URL
        or source["source_file_path"] != AMI_PARTITIONS_SOURCE_RELATIVE_PATH
        or source["source_sha256"] != AMI_PARTITIONS_SOURCE_SHA256
    ):
        raise ValueError("AMI partition source pin does not match the tracked pin")
    if source != metadata["official_partition_source"]:
        raise ValueError("AMI partition source metadata does not match quality item")
    source_file_path = source["source_file_path"]
    if (
        source_file_path not in selected_file_paths
        or metadata["official_partition_paths"] != [source_file_path]
        or metadata["official_partition_definitions"] != source["partition_definitions"]
    ):
        raise ValueError("AMI partition source bindings are invalid")
    meeting_universe_path = source["meeting_universe_source_file_path"]
    if meeting_universe_path not in selected_file_paths:
        raise ValueError("AMI partition meeting universe is not a selected hashed file")
    meeting_universe_ids = _ami_metadata_from_xml(
        project_root.joinpath(*meeting_universe_path.split("/"))
    )["meetings"]
    if not meeting_universe_ids:
        raise ValueError("AMI partition meeting universe has no meeting IDs")
    parsed_source = parse_ami_partition_source(
        project_root.joinpath(*source_file_path.split("/")),
        project_root=project_root,
        expected_sha256=source["source_sha256"],
        available_meeting_ids=meeting_universe_ids,
    )
    parsed_source["meeting_universe_source_file_path"] = meeting_universe_path
    if parsed_source != source:
        raise ValueError("AMI partition source does not match selected source")


def _verified_manifest(
    *,
    dataset_id: str,
    accessed_on: str,
    hash_inventory: dict[str, Any],
    hash_inventory_sha256: str,
    quality_inventory: dict[str, Any],
    quality_inventory_sha256: str,
) -> dict[str, Any]:
    manifest = _pending_manifest(dataset_id)
    selected_file_count = hash_inventory["selected_file_count"]
    selected_byte_count = hash_inventory["selected_byte_count"]
    included_file_count = quality_inventory["included_file_count"]
    excluded_file_count = quality_inventory["excluded_file_count"]
    manifest["accessed_on"] = accessed_on
    manifest["completion_status"] = "verified"
    manifest["local_file_hashes"].update({
        "inventory_sha256": hash_inventory_sha256,
        "selected_file_count": selected_file_count,
        "selected_byte_count": selected_byte_count,
    })
    manifest["hash_inventory"].update({
        "inventory_sha256": hash_inventory_sha256,
        "selected_file_count": selected_file_count,
        "selected_byte_count": selected_byte_count,
    })
    manifest["exclusion_inventory"].update({
        "quality_inventory_sha256": quality_inventory_sha256,
        "included_file_count": included_file_count,
        "excluded_file_count": excluded_file_count,
    })
    return validate_dataset_manifest(manifest)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _load_existing_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("existing dataset manifest is unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("existing dataset manifest is not an object")
    return payload


def _atomic_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def write_dataset_evidence(
    *,
    output_root: Path,
    accessed_on: str,
    materials: Mapping[str, Mapping[str, Any]],
    project_root: Path = ROOT,
) -> list[Path]:
    resolved_project_root = Path(project_root).resolve(strict=True)
    resolved_output_root = _guard_output_root(output_root, resolved_project_root)
    canonical_date = _canonical_access_date(accessed_on)
    if not isinstance(materials, Mapping) or set(materials) != set(
        SELECTED_PUBLIC_DATASETS
    ):
        raise ValueError("materials must contain exactly the selected public datasets")

    artifact_bytes: dict[Path, bytes] = {}
    for dataset_id in SELECTED_PUBLIC_DATASETS:
        material = materials[dataset_id]
        if not isinstance(material, Mapping) or set(material) != {
            "hash_inventory",
            "quality_inventory",
        }:
            raise ValueError("dataset material evidence fields mismatch")
        hash_inventory = material["hash_inventory"]
        quality_inventory = material["quality_inventory"]
        if not isinstance(hash_inventory, dict):
            raise ValueError("hash inventory must be an object")
        if hash_inventory.get("dataset_id") != dataset_id:
            raise ValueError("hash inventory dataset_id mismatch")
        validate_hash_inventory(hash_inventory, resolved_project_root)
        if dataset_id == CREMA_DATASET_ID:
            for entry in hash_inventory["files"]:
                path = entry["path"]
                if (
                    path.startswith("AudioWAV/")
                    or "/AudioWAV/" in path
                ) and "git_lfs_oid_sha256" not in entry:
                    raise ValueError(
                        "CREMA hash inventory is missing Git LFS OID evidence"
                    )
        selected_file_paths = {
            entry["path"]
            for entry in hash_inventory["files"]
        }
        _validate_quality_inventory(
            quality_inventory,
            dataset_id=dataset_id,
            selected_file_paths=selected_file_paths,
        )
        if dataset_id == AMI_DATASET_ID:
            _validate_ami_partition_source_bindings(
                quality_inventory,
                selected_file_paths=selected_file_paths,
                project_root=resolved_project_root,
            )
        hash_bytes = canonical_inventory_bytes(hash_inventory)
        quality_bytes = canonical_inventory_bytes(quality_inventory)
        manifest = _verified_manifest(
            dataset_id=dataset_id,
            accessed_on=canonical_date,
            hash_inventory=hash_inventory,
            hash_inventory_sha256=_sha256_bytes(hash_bytes),
            quality_inventory=quality_inventory,
            quality_inventory_sha256=_sha256_bytes(quality_bytes),
        )
        manifest_bytes = canonical_inventory_bytes(manifest)
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.manifest.json"
        ] = manifest_bytes
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.hashes.json"
        ] = hash_bytes
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.quality.json"
        ] = quality_bytes

    for dataset_id in SELECTED_PUBLIC_DATASETS:
        manifest_path = resolved_output_root / f"{dataset_id}.manifest.json"
        proposed_manifest_bytes = artifact_bytes[manifest_path]
        existing_manifest = _load_existing_manifest(manifest_path)
        if existing_manifest is None:
            continue
        if existing_manifest.get("completion_status") == "verified":
            existing_version = existing_manifest.get("manifest_version")
            proposed_version = json.loads(
                proposed_manifest_bytes.decode("utf-8")
            )["manifest_version"]
            if (
                existing_version == proposed_version
                and manifest_path.read_bytes() != proposed_manifest_bytes
            ):
                raise ValueError("verified_manifest_version_is_immutable")
            if existing_version != proposed_version:
                raise ValueError("verified_manifest_version_is_immutable")
            for suffix in ("hashes", "quality"):
                evidence_path = resolved_output_root / f"{dataset_id}.{suffix}.json"
                if (
                    evidence_path.exists()
                    and evidence_path.read_bytes() != artifact_bytes[evidence_path]
                ):
                    raise ValueError("verified_manifest_version_is_immutable")

    resolved_output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(artifact_bytes, key=lambda item: item.name):
        payload = artifact_bytes[path]
        if not path.exists() or path.read_bytes() != payload:
            _atomic_replace(path, payload)
        written.append(path)
    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build offline EMOTION-STATE public dataset evidence.",
        allow_abbrev=False,
    )
    parser.add_argument("--crema-root")
    parser.add_argument("--ami-archive")
    parser.add_argument("--ami-extract-root")
    parser.add_argument("--ami-partitions-source")
    parser.add_argument("--accessed-on")
    parser.add_argument(
        "--output-root",
        default=OUTPUT_DATASET_ROOT.as_posix(),
    )
    parser.add_argument(
        "--mode",
        choices=("list-ami", "write-evidence"),
        required=True,
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: Path = ROOT,
    git_command: GitCommand = _run_git_command,
    crema_expected_revision: str = CREMA_PROFILE_IDENTITY["source_revision"],
) -> int:
    try:
        args = parse_args(argv)
        resolved_project_root = Path(project_root).resolve(strict=True)
        if args.ami_archive is None:
            raise ValueError("--ami-archive is required")
        if args.ami_extract_root is None:
            raise ValueError("--ami-extract-root is required")
        ami_archive = _guard_public_path(
            args.ami_archive,
            project_root=resolved_project_root,
            field="ami-archive",
            must_exist=True,
            must_be_directory=False,
        )
        ami_extract_root = _guard_public_path(
            args.ami_extract_root,
            project_root=resolved_project_root,
            field="ami-extract-root",
            must_exist=False,
        )
        if args.mode == "list-ami":
            inspection = inspect_ami_archive(ami_archive, ami_extract_root)
            for member in inspection["members"]:
                print(f"{member['path']}\t{member['classification']}")
            return 0

        if args.crema_root is None:
            raise ValueError("--crema-root is required for write-evidence")
        if args.accessed_on is None:
            raise ValueError("--accessed-on is required for write-evidence")
        crema_root = _guard_public_path(
            args.crema_root,
            project_root=resolved_project_root,
            field="crema-root",
            must_exist=True,
            must_be_directory=True,
        )
        output_root = _guard_output_root(args.output_root, resolved_project_root)
        if args.ami_partitions_source is None:
            raise ValueError("--ami-partitions-source is required for write-evidence")
        ami_partitions_source = _guard_public_path(
            args.ami_partitions_source,
            project_root=resolved_project_root,
            field="ami-partitions-source",
            must_exist=True,
            must_be_directory=False,
        )
        accessed_on = _canonical_access_date(args.accessed_on)
        crema_lfs_oids = discover_crema_lfs_oids(
            crema_root,
            project_root=resolved_project_root,
            expected_revision=crema_expected_revision,
            git_command=git_command,
        )
        crema_material = validate_crema_material(
            crema_root,
            project_root=resolved_project_root,
            git_lfs_oids_by_path=crema_lfs_oids,
        )
        extraction = safe_extract_ami_archive(ami_archive, ami_extract_root)
        materials = {
            CREMA_DATASET_ID: crema_material,
            AMI_DATASET_ID: validate_ami_material(
                ami_extract_root,
                archive_path=ami_archive,
                extraction=extraction,
                partitions_source_path=ami_partitions_source,
                project_root=resolved_project_root,
            ),
        }
        write_dataset_evidence(
            output_root=output_root,
            accessed_on=accessed_on,
            materials=materials,
            project_root=resolved_project_root,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"offline dataset verifier failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
