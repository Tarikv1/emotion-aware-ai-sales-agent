from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from typing import Any

from scripts.validate_emotion_state_002_phase_b import (
    EXPECTED_DATASET_EVIDENCE,
    EXPECTED_EVIDENCE_IDENTITY_SHA256,
    EXPECTED_CONFIG,
    EXPECTED_METRIC_DEFINITIONS,
    EXPECTED_SLICE_DEFINITIONS,
    MINIMUM_UNIQUE_ACTORS,
    validate_evaluation_result,
    validate_published_ami_aggregate,
)


TRACKED_DATASET_EVIDENCE_FILENAMES = (
    "crema-d-v1.0-audio-wav.manifest.json",
    "crema-d-v1.0-audio-wav.hashes.json",
    "crema-d-v1.0-audio-wav.quality.json",
    "ami-manual-annotations-v1.6.2.manifest.json",
    "ami-manual-annotations-v1.6.2.hashes.json",
    "ami-manual-annotations-v1.6.2.quality.json",
)
_EXPECTED_TRACKED_SHA256 = {
    "crema-d-v1.0-audio-wav.manifest.json": EXPECTED_DATASET_EVIDENCE[
        "crema_d"
    ]["manifest_sha256"],
    "crema-d-v1.0-audio-wav.hashes.json": EXPECTED_DATASET_EVIDENCE[
        "crema_d"
    ]["hash_inventory_sha256"],
    "crema-d-v1.0-audio-wav.quality.json": EXPECTED_DATASET_EVIDENCE[
        "crema_d"
    ]["quality_inventory_sha256"],
    "ami-manual-annotations-v1.6.2.manifest.json": (
        EXPECTED_DATASET_EVIDENCE["ami"]["manifest_sha256"]
    ),
    "ami-manual-annotations-v1.6.2.hashes.json": (
        EXPECTED_DATASET_EVIDENCE["ami"]["hash_inventory_sha256"]
    ),
    "ami-manual-annotations-v1.6.2.quality.json": (
        EXPECTED_DATASET_EVIDENCE["ami"]["quality_inventory_sha256"]
    ),
}
_AMI_ARCHIVE_PATH = (
    "data/public/emotion-state/ami-manual-annotations-v1.6.2/"
    "ami_manual_1.6.2.zip"
)
_AMI_PARTITION_SOURCE_PATH = (
    "data/public/emotion-state/ami-manual-annotations-v1.6.2/"
    "official-partitions/datasets.shtml"
)
_AMI_PARTITION_SOURCE_SHA256 = (
    "30D038F540A91BA6E68133E8FDFAA1D2B4C1B7291F871B0D4821EA04F4C776ED"
)
_AMI_INCLUDED_CLASSIFICATIONS = {
    "downloaded_archive": 1,
    "manual_nxt_metadata": 3,
    "official_partition_metadata": 1,
    "dialogue_act": 695,
    "speaker_aligned_orthographic_transcript": 687,
    "timing_link": 687,
}
_AMI_CORE_CLASSIFICATIONS = frozenset(
    {
        "dialogue_act",
        "speaker_aligned_orthographic_transcript",
        "timing_link",
    }
)


class PublicMaterialPrerequisiteError(ValueError):
    """A tracked-evidence blocker that must fail before public material access."""


_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_PRIVATE_AGGREGATE_KEYS = frozenset(
    {
        "row_id",
        "row_ids",
        "actor_id",
        "actor_ids",
        "participant_id",
        "participant_ids",
        "meeting_id",
        "meeting_ids",
        "clip_stem",
        "clip_stems",
        "filename",
        "filenames",
        "file_path",
        "file_paths",
        "source_path",
        "source_paths",
        "path",
        "paths",
        "probabilities",
        "labels",
        "sentences",
        "transcript",
        "transcripts",
        "utterance_text",
        "raw_text",
        "audio",
    }
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


def _canonical_digest(value: Any) -> str:
    try:
        content = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox aggregate is not canonical JSON"
        ) from error
    return _sha256(content)


def validate_aggregate_privacy(payload: Any) -> None:
    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for raw_key, item in value.items():
                if type(raw_key) is not str:
                    raise PublicMaterialPrerequisiteError(
                        "aggregate key must be a string"
                    )
                key = raw_key.casefold()
                if (
                    key in _PRIVATE_AGGREGATE_KEYS
                    or key.endswith("_path")
                    or key.endswith("_filename")
                ):
                    raise PublicMaterialPrerequisiteError(
                        "private identifier, row, text, or path field is blocked"
                    )
                visit(item)
            for count_key in (
                "unique_actor_count",
                "unique_participant_count",
            ):
                if count_key not in value:
                    continue
                count = value[count_key]
                if type(count) is not int or count < 0:
                    raise PublicMaterialPrerequisiteError(
                        "published contributor count is invalid"
                    )
                suppressed = value.get("suppressed")
                has_published_value = (
                    "value" not in value or value.get("value") is not None
                )
                if (
                    count < MINIMUM_UNIQUE_ACTORS
                    and suppressed is not True
                    and has_published_value
                ):
                    raise PublicMaterialPrerequisiteError(
                        "published aggregate cell has fewer than ten contributors"
                    )
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if type(value) is str and (
            "\\" in value
            or "/" in value
            or re.search(r"(?i)\.(?:wav|xml|csv)(?:$|[?#])", value)
            or re.match(r"^[A-Za-z]:", value)
        ):
            raise PublicMaterialPrerequisiteError(
                "private identifier, row, text, or path value is blocked"
            )

    visit(payload)


def build_non_lockbox_review_packet(
    *,
    diagnostic_aggregate: Mapping[str, Any],
    ami_aggregate: Mapping[str, Any],
    split_manifest_sha256: str,
) -> dict[str, Any]:
    if (
        type(split_manifest_sha256) is not str
        or _SHA256_PATTERN.fullmatch(split_manifest_sha256) is None
    ):
        raise PublicMaterialPrerequisiteError(
            "split manifest identity is invalid"
        )
    diagnostic = copy.deepcopy(dict(diagnostic_aggregate))
    ami = copy.deepcopy(dict(ami_aggregate))
    try:
        validate_evaluation_result(
            diagnostic,
            expected_role="balanced_diagnostic",
        )
        validate_published_ami_aggregate(ami)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"non-lockbox aggregate validation failed: {error}"
        ) from error
    if diagnostic.get("final_decision_eligible") is not False:
        raise PublicMaterialPrerequisiteError(
            "balanced diagnostic cannot be final-decision eligible"
        )
    validate_aggregate_privacy(diagnostic)
    validate_aggregate_privacy(ami)
    packet: dict[str, Any] = {
        "schema_id": "emotion-state-phase-b-non-lockbox-review-v2",
        "schema_version": 2,
        "configuration_sha256": EXPECTED_EVIDENCE_IDENTITY_SHA256[
            "configuration_sha256"
        ],
        "split_manifest_sha256": split_manifest_sha256,
        "model_settings": copy.deepcopy(EXPECTED_CONFIG["model"]),
        "metric_definitions": copy.deepcopy(EXPECTED_METRIC_DEFINITIONS),
        "slice_definitions": copy.deepcopy(EXPECTED_SLICE_DEFINITIONS),
        "minimum_unique_contributors_per_cell": MINIMUM_UNIQUE_ACTORS,
        "lockbox_access": {
            "open_count": 0,
            "label_reads": 0,
            "feature_reads": 0,
            "audio_reads": 0,
        },
        "final_decision_eligible": False,
        "diagnostic_aggregate": diagnostic,
        "diagnostic_aggregate_sha256": _canonical_digest(diagnostic),
        "ami_aggregate": ami,
        "ami_aggregate_sha256": _canonical_digest(ami),
    }
    packet["review_sha256"] = _canonical_digest(packet)
    return packet


def validate_non_lockbox_review_packet(
    payload: Any,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review packet must be a mapping"
        )
    packet = copy.deepcopy(dict(payload))
    expected_keys = {
        "schema_id",
        "schema_version",
        "configuration_sha256",
        "split_manifest_sha256",
        "model_settings",
        "metric_definitions",
        "slice_definitions",
        "minimum_unique_contributors_per_cell",
        "lockbox_access",
        "final_decision_eligible",
        "diagnostic_aggregate",
        "diagnostic_aggregate_sha256",
        "ami_aggregate",
        "ami_aggregate_sha256",
        "review_sha256",
    }
    if set(packet) != expected_keys:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review packet fields do not match"
        )
    if (
        packet["schema_id"]
        != "emotion-state-phase-b-non-lockbox-review-v2"
        or packet["schema_version"] != 2
        or type(packet["schema_version"]) is not int
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review packet schema does not match"
        )
    if (
        packet["configuration_sha256"]
        != EXPECTED_EVIDENCE_IDENTITY_SHA256["configuration_sha256"]
    ):
        raise PublicMaterialPrerequisiteError(
            "configuration identity does not match"
        )
    if packet["model_settings"] != EXPECTED_CONFIG["model"]:
        raise PublicMaterialPrerequisiteError(
            "model settings do not match the frozen configuration"
        )
    if packet["metric_definitions"] != EXPECTED_METRIC_DEFINITIONS:
        raise PublicMaterialPrerequisiteError(
            "metric definitions do not match"
        )
    if packet["slice_definitions"] != EXPECTED_SLICE_DEFINITIONS:
        raise PublicMaterialPrerequisiteError(
            "slice definitions do not match"
        )
    if packet["minimum_unique_contributors_per_cell"] != MINIMUM_UNIQUE_ACTORS:
        raise PublicMaterialPrerequisiteError(
            "contributor floor does not match"
        )
    if (
        type(packet["split_manifest_sha256"]) is not str
        or _SHA256_PATTERN.fullmatch(packet["split_manifest_sha256"])
        is None
    ):
        raise PublicMaterialPrerequisiteError(
            "split manifest identity is invalid"
        )
    if packet["lockbox_access"] != {
        "open_count": 0,
        "label_reads": 0,
        "feature_reads": 0,
        "audio_reads": 0,
    }:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review must record zero lockbox reads"
        )
    if packet["final_decision_eligible"] is not False:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review cannot be decision eligible"
        )
    try:
        validate_evaluation_result(
            packet["diagnostic_aggregate"],
            expected_role="balanced_diagnostic",
        )
        validate_published_ami_aggregate(packet["ami_aggregate"])
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"non-lockbox aggregate validation failed: {error}"
        ) from error
    validate_aggregate_privacy(packet["diagnostic_aggregate"])
    validate_aggregate_privacy(packet["ami_aggregate"])
    if (
        _canonical_digest(packet["diagnostic_aggregate"])
        != packet["diagnostic_aggregate_sha256"]
        or _canonical_digest(packet["ami_aggregate"])
        != packet["ami_aggregate_sha256"]
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox aggregate commitment changed"
        )
    review_sha256 = packet.pop("review_sha256")
    if (
        type(review_sha256) is not str
        or _SHA256_PATTERN.fullmatch(review_sha256) is None
        or _canonical_digest(packet) != review_sha256
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review commitment changed"
        )
    packet["review_sha256"] = review_sha256
    return packet


def _strict_json_object(content: bytes, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {value}")
            ),
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise PublicMaterialPrerequisiteError(
            f"{label} tracked evidence is invalid"
        ) from error
    if not isinstance(payload, dict):
        raise PublicMaterialPrerequisiteError(
            f"{label} tracked evidence must be an object"
        )
    return payload


def _validate_ami_inventory(
    manifest: Mapping[str, Any],
    hashes: Mapping[str, Any],
    quality: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        manifest.get("dataset_id") != "ami-manual-annotations-v1.6.2"
        or manifest.get("completion_status") != "verified"
        or manifest.get("runtime_influence_allowed") is not False
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI manifest identity or boundary does not match"
        )
    files = hashes.get("files")
    if (
        hashes.get("dataset_id") != "ami-manual-annotations-v1.6.2"
        or hashes.get("algorithm") != "SHA-256"
        or hashes.get("selected_file_count") != 2074
        or not isinstance(files, list)
        or len(files) != 2074
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI selected hash inventory does not match"
        )
    identities: dict[str, str] = {}
    for row in files:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "size_bytes"}
            or type(row["path"]) is not str
            or type(row["sha256"]) is not str
            or type(row["size_bytes"]) is not int
            or row["size_bytes"] <= 0
            or row["path"] in identities
        ):
            raise PublicMaterialPrerequisiteError(
                "AMI selected hash row is invalid"
            )
        identities[row["path"]] = row["sha256"]
    if (
        identities.get(_AMI_ARCHIVE_PATH)
        != EXPECTED_DATASET_EVIDENCE["ami"]["archive_sha256"]
        or identities.get(_AMI_PARTITION_SOURCE_PATH)
        != _AMI_PARTITION_SOURCE_SHA256
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI archive or official partition identity does not match"
        )

    items = quality.get("items")
    quarantine = quality.get("dependency_quarantine")
    if (
        quality.get("dataset_id") != "ami-manual-annotations-v1.6.2"
        or quality.get("included_file_count") != 2074
        or quality.get("excluded_file_count") != 3086
        or not isinstance(items, list)
        or not isinstance(quarantine, list)
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI quality inventory counts do not match"
        )
    included = Counter(
        row.get("classification")
        for row in items
        if isinstance(row, dict) and row.get("disposition") == "included"
    )
    if dict(included) != _AMI_INCLUDED_CLASSIFICATIONS:
        raise PublicMaterialPrerequisiteError(
            "AMI selected classifications do not match"
        )
    core_paths = {
        row.get("selected_file_path")
        for row in items
        if isinstance(row, dict)
        and row.get("disposition") == "included"
        and row.get("classification") in _AMI_CORE_CLASSIFICATIONS
    }
    quarantine_paths = {
        row.get("path")
        for row in quarantine
        if isinstance(row, dict)
        and set(row) == {"path", "reason"}
        and row.get("reason") == "required_participant_identity_missing"
    }
    if (
        len(quarantine) != 2069
        or len(quarantine_paths) != 2069
        or core_paths != quarantine_paths
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI dependency quarantine identity does not match"
        )
    raise PublicMaterialPrerequisiteError(
        "2069 AMI selected annotation files remain quarantined because "
        "required participant identity is missing"
    )


def validate_tracked_public_evidence(
    evidence: Mapping[str, bytes],
) -> dict[str, Any]:
    if not isinstance(evidence, Mapping) or set(evidence) != set(
        TRACKED_DATASET_EVIDENCE_FILENAMES
    ):
        raise PublicMaterialPrerequisiteError(
            "tracked dataset evidence set does not match"
        )
    parsed: dict[str, dict[str, Any]] = {}
    for name in TRACKED_DATASET_EVIDENCE_FILENAMES:
        content = evidence[name]
        if type(content) is not bytes:
            raise PublicMaterialPrerequisiteError(
                f"{name} tracked evidence must be bytes"
            )
        if _sha256(content) != _EXPECTED_TRACKED_SHA256[name]:
            raise PublicMaterialPrerequisiteError(
                f"{name} tracked evidence identity changed"
            )
        parsed[name] = _strict_json_object(content, name)
    return _validate_ami_inventory(
        parsed["ami-manual-annotations-v1.6.2.manifest.json"],
        parsed["ami-manual-annotations-v1.6.2.hashes.json"],
        parsed["ami-manual-annotations-v1.6.2.quality.json"],
    )
