from __future__ import annotations

import hashlib
import re
import unicodedata
from copy import deepcopy
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

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

_DATASET_PROFILES: dict[str, dict[str, Any]] = {
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
}

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


class PublicDatasetContractError(ValueError):
    pass


def dataset_profile(dataset_id: str) -> dict[str, Any]:
    if not isinstance(dataset_id, str):
        raise ValueError(f"unknown public dataset: {dataset_id}")
    try:
        return deepcopy(_DATASET_PROFILES[dataset_id])
    except KeyError as exc:
        raise ValueError(f"unknown public dataset: {dataset_id}") from exc


def _require_exact_object(value: Any, fields: frozenset[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise PublicDatasetContractError(f"{field} fields mismatch")
    return value


def _require_nonnegative_integer(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise PublicDatasetContractError(f"{field} must be a nonnegative integer")
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
    if hash_reference["schema_version"] != 1:
        raise PublicDatasetContractError("hash_inventory schema_version is invalid")
    if hash_reference["path_normalization"] != "project-relative-posix-nfc":
        raise PublicDatasetContractError("hash_inventory path_normalization is invalid")
    if hash_reference["ordering"] != "ordinal-by-normalized-path":
        raise PublicDatasetContractError("hash_inventory ordering is invalid")
    if exclusion_reference["schema_id"] != "emotion-state-dataset-quality-inventory-reference-v1":
        raise PublicDatasetContractError("exclusion_inventory schema_id is invalid")
    if exclusion_reference["schema_version"] != 1:
        raise PublicDatasetContractError("exclusion_inventory schema_version is invalid")
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
    if payload["inventory_version"] != 1:
        raise PublicDatasetContractError("inventory_version must be 1")
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
