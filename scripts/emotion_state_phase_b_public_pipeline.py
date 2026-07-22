from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scripts.emotion_state_phase_b_evaluation import (
        ValidatedPartitionAuthority,
    )

from scripts.emotion_state_public_dataset_contracts import (
    PublicDatasetContractError,
    classify_ami_member,
    validate_dataset_manifest,
)
from scripts.validate_emotion_state_002_phase_b import (
    CLASS_ORDER,
    EXPECTED_DATASET_EVIDENCE,
    EXPECTED_EVIDENCE_IDENTITY_SHA256,
    EXPECTED_CONFIG,
    EXPECTED_ENVIRONMENT_LOCK,
    EXPECTED_FEATURE_SCHEMA,
    EXPECTED_METRIC_DEFINITIONS,
    EXPECTED_PHASE_A_BINDING,
    EXPECTED_RAW_CSV_SHA256,
    EXPECTED_SLICE_DEFINITIONS,
    EXPECTED_SPLIT_SCHEMA,
    MINIMUM_UNIQUE_ACTORS,
    MODEL_KEYS,
    canonical_payload_sha256,
    validate_config,
    validate_config_feature_schema_binding,
    validate_crema_label_ledger,
    validate_ami_mechanics_aggregates_v2,
    validate_environment_lock,
    validate_evaluation_result,
    validate_feature_schema,
    validate_phase_b_input_ledger,
    validate_phase_b_partition_authority_cache,
    validate_phase_b_split_manifest,
    validate_published_ami_aggregate_v2,
    validate_provenance_payload,
    validate_split_schema,
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
_CREMA_DATASET_ID = "crema-d-v1.0-audio-wav"
_AMI_DATASET_ID = "ami-manual-annotations-v1.6.2"
_CREMA_ROOT = "data/public/emotion-state/crema-d-v1.0/repository/"
_CREMA_AUDIO_ROOT = f"{_CREMA_ROOT}AudioWAV/"
_AMI_ROOT = "data/public/emotion-state/ami-manual-annotations-v1.6.2/"
_AMI_EXTRACTED_ROOT = f"{_AMI_ROOT}extracted/"
_AMI_PARTITION_SOURCE_URL = (
    "https://groups.inf.ed.ac.uk/ami/corpus/datasets.shtml"
)
_AMI_MEETING_UNIVERSE_PATH = (
    f"{_AMI_EXTRACTED_ROOT}corpusResources/meetings.xml"
)
_AMI_PARTICIPANTS_PATH = (
    f"{_AMI_EXTRACTED_ROOT}corpusResources/participants.xml"
)
_AMI_METADATA_PATH = f"{_AMI_EXTRACTED_ROOT}AMI-metadata.xml"
_AMI_EXCLUDED_SOURCE_PATHS = frozenset({
    _AMI_ARCHIVE_PATH,
    _AMI_PARTITION_SOURCE_PATH,
    _AMI_METADATA_PATH,
})
_AMI_PARSER_ANNOTATION_FILENAME = re.compile(
    r"^(?P<meeting>[A-Z]{2}\d{4}[a-e]?)\.(?P<speaker>[A-Z])\."
    r"(?P<family>words|segments|dialog-act)\.xml$"
)
_AMI_ADJACENCY_FILENAME = re.compile(
    r"^(?P<meeting>[A-Z]{2}\d{4}[a-e]?)\.adjacency-pairs\.xml$"
)
_AMI_OUTSIDE_PARTITION_SOURCE_PATHS = frozenset({
    *{
        f"{_AMI_EXTRACTED_ROOT}words/IB4005.{speaker}.words.xml"
        for speaker in "ABCD"
    },
    *{
        f"{_AMI_EXTRACTED_ROOT}segments/IB4005.{speaker}.segments.xml"
        for speaker in "ABCD"
    },
})
_MANIFEST_FIELDS = frozenset(
    {
        "access_restrictions",
        "accessed_on",
        "canonical_source_url",
        "completion_status",
        "dataset_id",
        "dependency_keys",
        "domain",
        "domain_limitations",
        "excluded_labels",
        "exclusion_inventory",
        "hash_inventory",
        "known_issues",
        "language",
        "local_file_hashes",
        "manifest_version",
        "permitted_research_lanes",
        "project_label_mapping",
        "quality_rules",
        "redistribution_status",
        "release_or_version",
        "release_published_at",
        "runtime_influence_allowed",
        "selected_artifacts",
        "source_label",
        "source_labels",
        "source_revision",
        "terms_or_license",
    }
)
_HASH_INVENTORY_FIELDS = frozenset(
    {
        "algorithm",
        "dataset_id",
        "files",
        "inventory_version",
        "ordering",
        "path_normalization",
        "selected_byte_count",
        "selected_file_count",
    }
)
_QUALITY_FIELDS = frozenset(
    {
        "dataset_id",
        "dependency_quarantine",
        "excluded_file_count",
        "included_file_count",
        "items",
        "limitations",
        "quality_inventory_version",
        "source_metadata",
    }
)
_QUALITY_ITEM_FIELDS = frozenset(
    {
        "classification",
        "details",
        "disposition",
        "path",
        "reason",
        "selected_file_path",
    }
)
_CREMA_METADATA_IDENTITIES = {
    f"{_CREMA_ROOT}LICENSE.txt": (
        "A214F811B7C0AADB23ABEC19F27746B5A4277AA0E356F82EE7506E36CA9F97D2",
        317,
    ),
    f"{_CREMA_ROOT}README.md": (
        "CD6C9E59B60D6B1F96DE7330D8640892B891419F298EC13B240661C5D3105530",
        13173,
    ),
    f"{_CREMA_ROOT}SentenceFilenames.csv": (
        "BA8C2D1EC4A0B585CA003FFE37FD59CFF9A7E2D5B23389E4769B355FD363DFB7",
        177529,
    ),
    f"{_CREMA_ROOT}finishedResponses.csv": (
        "939D02D2DDDDDF575BBCCFFB80F14F1D110FDA88F092F2A68201994EB3BCB45B",
        22348253,
    ),
    f"{_CREMA_ROOT}processedResults/summaryTable.csv": (
        "1EA0E13D98853D920C7C51E69A72BA5BA42018F85A9B89B8B2CC1B53C1AA56A9",
        456491,
    ),
}
_CREMA_CLASSIFICATIONS = {
    ("included", "crema_pcm_wav"): (
        7441,
        "frozen_audio_wav_selection",
    ),
    ("included", "crema_release_metadata"): (
        5,
        "frozen_fixed_selection",
    ),
    ("excluded", "crema_demographic_metadata"): (
        1,
        "excluded_demographic_metadata",
    ),
    ("excluded", "crema_unselected_release_material"): (
        22365,
        "outside_frozen_selection",
    ),
    ("excluded", "crema_wav"): (
        1,
        "official_known_no_audio_issue",
    ),
}
_AMI_EXCLUDED_CLASSIFICATION_COUNTS = {
    "manual_annotation_abstractive": 142,
    "manual_annotation_argumentation": 565,
    "manual_annotation_configuration": 2,
    "manual_annotation_decision": 47,
    "manual_annotation_disfluency": 160,
    "manual_annotation_extractive": 274,
    "manual_annotation_focus": 56,
    "manual_annotation_hand_gesture": 61,
    "manual_annotation_head_gesture": 173,
    "manual_annotation_movement": 498,
    "manual_annotation_named_entities": 468,
    "manual_annotation_ontologies": 17,
    "manual_annotation_participant_roles": 20,
    "manual_annotation_participant_summaries": 323,
    "manual_annotation_root_licence": 1,
    "manual_annotation_root_manifest": 1,
    "manual_annotation_root_readme": 1,
    "manual_annotation_root_resource": 1,
    "manual_annotation_topics": 139,
    "manual_annotation_you_usages": 63,
    "speculative_emotion": 1,
    "unselected_release_material": 73,
}
_AMI_CLASSIFICATIONS = {
    **{
        ("included", classification): (
            count,
            (
                "archive_hashed_before_extraction"
                if classification == "downloaded_archive"
                else (
                    "selected_official_partition_source"
                    if classification == "official_partition_metadata"
                    else "selected_manual_annotation_material"
                )
            ),
        )
        for classification, count in _AMI_INCLUDED_CLASSIFICATIONS.items()
    },
    **{
        ("excluded", classification): (
            count,
            f"excluded_{classification}",
        )
        for classification, count in _AMI_EXCLUDED_CLASSIFICATION_COUNTS.items()
    },
}
_CREMA_FILENAME = re.compile(
    r"^(?P<actor>\d{4})_(?P<sentence>[A-Z0-9]{3})_"
    r"(?P<emotion>ANG|DIS|FEA|HAP|NEU|SAD)_"
    r"(?P<intensity>HI|LO|MD|XX)\.wav$"
)
_CREMA_EMOTION_LABELS = {
    "ANG": "anger",
    "DIS": "disgust",
    "FEA": "fear",
    "HAP": "happy",
    "NEU": "neutral",
    "SAD": "sad",
}
_WINDOWS_INVALID_COMPONENT_CHARACTERS = frozenset('<>:"\\|?*')
_WINDOWS_RESERVED_COMPONENTS = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)

AMI_FULL_CORPUS_ORDER = (
    "EN2001a", "EN2001b", "EN2001d", "EN2001e", "EN2002a", "EN2002b",
    "EN2002c", "EN2002d", "EN2003a", "EN2004a", "EN2005a", "EN2006a",
    "EN2006b", "EN2009b", "EN2009c", "EN2009d", "ES2002a", "ES2002b",
    "ES2002c", "ES2002d", "ES2003a", "ES2003b", "ES2003c", "ES2003d",
    "ES2004a", "ES2004b", "ES2004c", "ES2004d", "ES2005a", "ES2005b",
    "ES2005c", "ES2005d", "ES2006a", "ES2006b", "ES2006c", "ES2006d",
    "ES2007a", "ES2007b", "ES2007c", "ES2007d", "ES2008a", "ES2008b",
    "ES2008c", "ES2008d", "ES2009a", "ES2009b", "ES2009c", "ES2009d",
    "ES2010a", "ES2010b", "ES2010c", "ES2010d", "ES2011a", "ES2011b",
    "ES2011c", "ES2011d", "ES2012a", "ES2012b", "ES2012c", "ES2012d",
    "ES2013a", "ES2013b", "ES2013c", "ES2013d", "ES2014a", "ES2014b",
    "ES2014c", "ES2014d", "ES2015a", "ES2015b", "ES2015c", "ES2015d",
    "ES2016a", "ES2016b", "ES2016c", "ES2016d", "IB4001", "IB4002",
    "IB4003", "IB4004", "IB4010", "IB4011", "IN1001", "IN1002",
    "IN1005", "IN1007", "IN1008", "IN1009", "IN1012", "IN1013",
    "IN1014", "IN1016", "IS1000a", "IS1000b", "IS1000c", "IS1000d",
    "IS1001a", "IS1001b", "IS1001c", "IS1001d", "IS1002b", "IS1002c",
    "IS1002d", "IS1003a", "IS1003b", "IS1003c", "IS1003d", "IS1004a",
    "IS1004b", "IS1004c", "IS1004d", "IS1005a", "IS1005b", "IS1005c",
    "IS1006a", "IS1006b", "IS1006c", "IS1006d", "IS1007a", "IS1007b",
    "IS1007c", "IS1007d", "IS1008a", "IS1008b", "IS1008c", "IS1008d",
    "IS1009a", "IS1009b", "IS1009c", "IS1009d", "TS3003a", "TS3003b",
    "TS3003c", "TS3003d", "TS3004a", "TS3004b", "TS3004c", "TS3004d",
    "TS3005a", "TS3005b", "TS3005c", "TS3005d", "TS3006a", "TS3006b",
    "TS3006c", "TS3006d", "TS3007a", "TS3007b", "TS3007c", "TS3007d",
    "TS3008a", "TS3008b", "TS3008c", "TS3008d", "TS3009a", "TS3009b",
    "TS3009c", "TS3009d", "TS3010a", "TS3010b", "TS3010c", "TS3010d",
    "TS3011a", "TS3011b", "TS3011c", "TS3011d", "TS3012a", "TS3012b",
    "TS3012c", "TS3012d",
)
AMI_FULL_ONLY_ORDER = (
    "EN2001a", "EN2001b", "EN2001d", "EN2001e", "EN2002a", "EN2002b",
    "EN2002c", "EN2002d", "EN2003a", "EN2004a", "EN2005a", "EN2006a",
    "EN2006b", "EN2009b", "EN2009c", "EN2009d", "IB4001", "IB4002",
    "IB4003", "IB4004", "IB4010", "IB4011", "IN1001", "IN1002",
    "IN1005", "IN1007", "IN1008", "IN1009", "IN1012", "IN1013",
    "IN1014", "IN1016",
)
AMI_EXPECTED_ANNOTATION_PATHS = frozenset({
    *{
        f"{_AMI_EXTRACTED_ROOT}words/{meeting}.{speaker}.words.xml"
        for meeting in (*AMI_FULL_CORPUS_ORDER, "IB4005")
        for speaker in "ABCD"
    },
    *{
        f"{_AMI_EXTRACTED_ROOT}segments/{meeting}.{speaker}.segments.xml"
        for meeting in (*AMI_FULL_CORPUS_ORDER, "IB4005")
        for speaker in "ABCD"
    },
    *{
        f"{_AMI_EXTRACTED_ROOT}{family}/{meeting}.E.{suffix}"
        for family, suffix in (("words", "words.xml"), ("segments", "segments.xml"))
        for meeting in ("EN2001a", "EN2001d", "EN2001e")
    },
    *{
        f"{_AMI_EXTRACTED_ROOT}dialogueActs/{meeting}.{speaker}.dialog-act.xml"
        for meeting in (
            *(
                item
                for item in AMI_FULL_CORPUS_ORDER
                if item not in set(AMI_FULL_ONLY_ORDER)
            ),
            "IB4003",
        )
        for speaker in "ABCD"
    },
    *{
        f"{_AMI_EXTRACTED_ROOT}dialogueActs/{meeting}.adjacency-pairs.xml"
        for meeting in (
            *(
                item
                for item in AMI_FULL_CORPUS_ORDER
                if item not in set(AMI_FULL_ONLY_ORDER)
            ),
            "IB4003",
        )
    },
})


@dataclass(frozen=True, slots=True)
class SourceByteIdentity:
    project_relative_path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class TrackedPublicAuthority:
    crema_audio: tuple[SourceByteIdentity, ...]
    crema_finished_responses: SourceByteIdentity
    crema_summary_table: SourceByteIdentity
    ami_files: tuple[SourceByteIdentity, ...]
    ami_partition_membership: tuple[
        tuple[str, tuple[str, ...]], ...
    ]
    ami_official_order: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductionPreflightArtifacts:
    source_authority_commitment_sha256: str
    input_ledger: dict[str, Any]
    split_manifest: dict[str, Any]
    partition_authority_caches: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ProductionNonLockboxArtifacts:
    feature_caches: dict[str, dict[str, Any]]
    ami_evidence: dict[str, Any]
    review_packet: dict[str, Any]


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
EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS = {
    "training_discovery": 2491,
    "calibration": 959,
    "balanced_diagnostic": 939,
}
EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT = 4389
EXPECTED_PRODUCTION_FINAL_LOCKBOX_RECORD_COUNT = 2181
EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT = 6570
NON_LOCKBOX_ROLE_ORDER = tuple(EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS)
ARTIFACT_CACHE_COMMITMENT_ORDER = (*NON_LOCKBOX_ROLE_ORDER, "ami_evidence")
ACOUSTIC_FEATURE_CACHE_SCHEMA_ID = (
    "emotion-state-phase-b-acoustic-feature-cache-v1"
)
AMI_EVIDENCE_CACHE_SCHEMA_ID = "emotion-state-phase-b-ami-evidence-cache-v1"
SLICE_ANALYSIS_SCHEMA_ID = "emotion-state-phase-b-slice-analysis-v2"
NON_LOCKBOX_PACKET_SCHEMA_ID = "emotion-state-phase-b-non-lockbox-review-v4"
EXPECTED_AMI_SELECTED_SOURCE_COUNT = 1924
EXPECTED_DIAGNOSTIC_SLICE_COUNT = 25
_VOTE_SLICE_NAMES = (
    "vote_agreement:[0.00,0.50)",
    "vote_agreement:[0.50,0.75)",
    "vote_agreement:[0.75,1.00]",
)
_SILENCE_SLICE_NAMES = tuple(f"silence_ratio:Q{index}" for index in range(1, 5))
_SLICE_ANALYSIS_KEYS = frozenset(
    {
        "schema_id",
        "partition_role",
        "class_order",
        "instability_tolerance",
        "slices",
        "eligible_slice_reversal",
        "eligible_slice_instability",
        "probability_evidence_mint_sha256",
        "evaluation_evidence_mint_sha256",
        "provenance",
        "self_sha256",
    }
)
_SLICE_CELL_KEYS = frozenset(
    {
        "case_count",
        "unique_actor_count",
        "suppressed",
        "contributor_row_commitment_sha256",
        "contributor_actor_commitment_sha256",
        "model_macro_f1",
        "paired_macro_f1_lift",
    }
)
_FEATURE_CACHE_KEYS = (
    "schema_id",
    "schema_version",
    "partition_role",
    "configuration_sha256",
    "environment_lock_sha256",
    "feature_schema_sha256",
    "split_schema_sha256",
    "split_manifest_sha256",
    "assignment_sha256",
    "partition_authority_sha256",
    "tracked_public_authority_commitment_sha256",
    "upstream_acoustic_source_commitment_sha256",
    "feature_names",
    "records",
    "self_sha256",
)
_FEATURE_CACHE_RECORD_KEYS = (
    "clip_stem",
    "audio_sha256",
    "audio_size_bytes",
    "features",
)
_AMI_EVIDENCE_CACHE_KEYS = (
    "schema_id",
    "schema_version",
    "source_authority_sha256",
    "tracked_public_authority_commitment_sha256",
    "source_file_count",
    "meetings",
    "partition_membership",
    "official_order",
    "aggregate",
    "aggregate_sha256",
    "self_sha256",
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


def _matches_packet_contract_exactly(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, Mapping):
        if len(actual) != len(expected):
            return False
        for expected_key, expected_value in expected.items():
            exact_keys = tuple(
                actual_key
                for actual_key in actual
                if type(actual_key) is type(expected_key)
                and actual_key == expected_key
            )
            if len(exact_keys) != 1 or not _matches_packet_contract_exactly(
                actual[exact_keys[0]],
                expected_value,
            ):
                return False
        return True
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _matches_packet_contract_exactly(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )
    return actual == expected


def _has_exact_string_keys(
    value: Any,
    expected: Sequence[str] | set[str] | frozenset[str],
) -> bool:
    return (
        type(value) is dict
        and all(type(key) is str for key in value)
        and set(value) == set(expected)
    )


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


def _validate_diagnostic_identity_bindings(
    diagnostic: Mapping[str, Any],
    *,
    configuration_sha256: str,
    split_manifest_sha256: str,
) -> None:
    provenance = diagnostic["provenance"]
    if provenance["configuration_sha256"] != configuration_sha256:
        raise PublicMaterialPrerequisiteError(
            "configuration identity does not match diagnostic provenance"
        )
    if provenance["split_manifest_sha256"] != split_manifest_sha256:
        raise PublicMaterialPrerequisiteError(
            "split manifest identity does not match diagnostic provenance"
        )


def _acoustic_source_commitment(
    role: str,
    records: Sequence[Any],
) -> str:
    return _canonical_digest({
        "schema_id": "emotion-state-phase-b-acoustic-source-commitment-v1",
        "partition_role": role,
        "records": [
            {
                "clip_stem": record.label_record.clip_stem,
                "audio_sha256": record.audio_sha256,
                "audio_size_bytes": record.audio_size_bytes,
            }
            for record in records
        ],
    })


def _exact_feature_values(value: Any) -> dict[str, float]:
    from scripts.emotion_state_phase_b_features import FEATURE_NAMES

    if (
        not _has_exact_string_keys(value, set(FEATURE_NAMES))
        or tuple(value) != tuple(FEATURE_NAMES)
    ):
        raise PublicMaterialPrerequisiteError(
            "acoustic feature mapping order does not match"
        )
    if any(
        type(item) is not float or not math.isfinite(item)
        for item in value.values()
    ):
        raise PublicMaterialPrerequisiteError(
            "acoustic feature values must be finite built-in floats"
        )
    return dict(value)


def _feature_cache_role_records(
    *,
    authority: Any,
    role: str,
    validated_records: tuple[Any, ...] | None,
) -> tuple[Any, ...]:
    if validated_records is None:
        from scripts.emotion_state_phase_b_evaluation import (
            validated_partition_records,
        )

        return validated_partition_records(authority, role=role)
    if (
        type(validated_records) is not tuple
        or len(validated_records)
        != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
    ):
        raise PublicMaterialPrerequisiteError(
            "prevalidated feature-cache records do not match production algebra"
        )
    return validated_records


def _build_acoustic_feature_cache(
    *,
    role: str,
    authority: Any,
    feature_rows: Sequence[Mapping[str, float]],
    tracked_public_authority_commitment_sha256: str,
    environment_lock_sha256: str,
    feature_schema_sha256: str,
    split_schema_sha256: str,
    _validated_records: tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    from scripts.emotion_state_phase_b_features import FEATURE_NAMES

    if type(role) is not str or role not in NON_LOCKBOX_ROLE_ORDER:
        raise PublicMaterialPrerequisiteError(
            "feature cache partition role does not match"
        )
    records = _feature_cache_role_records(
        authority=authority,
        role=role,
        validated_records=_validated_records,
    )
    expected_count = EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
    if len(records) != expected_count:
        raise PublicMaterialPrerequisiteError(
            "feature cache authority count does not match production algebra"
        )
    if (
        isinstance(feature_rows, (str, bytes, Mapping))
        or not isinstance(feature_rows, Sequence)
        or len(feature_rows) != len(records)
    ):
        raise PublicMaterialPrerequisiteError(
            "feature cache rows do not match partition authority"
        )
    authority_payload = authority.to_payload()
    for name, digest in (
        (
            "tracked public authority commitment",
            tracked_public_authority_commitment_sha256,
        ),
        ("environment lock identity", environment_lock_sha256),
        ("feature schema identity", feature_schema_sha256),
        ("split schema identity", split_schema_sha256),
    ):
        _require_sha256(digest, name)
    cache_records = []
    for authority_record, raw_features in zip(records, feature_rows, strict=True):
        cache_records.append({
            "clip_stem": authority_record.label_record.clip_stem,
            "audio_sha256": authority_record.audio_sha256,
            "audio_size_bytes": authority_record.audio_size_bytes,
            "features": _exact_feature_values(raw_features),
        })
    cache: dict[str, Any] = {
        "schema_id": ACOUSTIC_FEATURE_CACHE_SCHEMA_ID,
        "schema_version": 1,
        "partition_role": role,
        "configuration_sha256": authority_payload["configuration_sha256"],
        "environment_lock_sha256": environment_lock_sha256,
        "feature_schema_sha256": feature_schema_sha256,
        "split_schema_sha256": split_schema_sha256,
        "split_manifest_sha256": authority_payload["split_manifest_sha256"],
        "assignment_sha256": authority_payload["assignment_sha256"],
        "partition_authority_sha256": authority_payload[
            "partition_authority_sha256"
        ],
        "tracked_public_authority_commitment_sha256": (
            tracked_public_authority_commitment_sha256
        ),
        "upstream_acoustic_source_commitment_sha256": (
            _acoustic_source_commitment(role, records)
        ),
        "feature_names": list(FEATURE_NAMES),
        "records": cache_records,
    }
    cache["self_sha256"] = canonical_payload_sha256(cache)
    return _validate_acoustic_feature_cache(
        cache,
        role=role,
        authority=authority,
        tracked_public_authority_commitment_sha256=(
            tracked_public_authority_commitment_sha256
        ),
        environment_lock_sha256=environment_lock_sha256,
        feature_schema_sha256=feature_schema_sha256,
        split_schema_sha256=split_schema_sha256,
        _validated_records=records,
    )


def _validate_acoustic_feature_cache(
    payload: Any,
    *,
    role: str,
    authority: Any,
    tracked_public_authority_commitment_sha256: str,
    environment_lock_sha256: str,
    feature_schema_sha256: str,
    split_schema_sha256: str,
    _validated_records: tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    from scripts.emotion_state_phase_b_features import FEATURE_NAMES

    if (
        not _has_exact_string_keys(payload, set(_FEATURE_CACHE_KEYS))
        or tuple(payload) != _FEATURE_CACHE_KEYS
    ):
        raise PublicMaterialPrerequisiteError("feature cache fields do not match")
    if type(role) is not str or role not in NON_LOCKBOX_ROLE_ORDER:
        raise PublicMaterialPrerequisiteError(
            "feature cache partition role does not match"
        )
    cache = copy.deepcopy(payload)
    records = _feature_cache_role_records(
        authority=authority,
        role=role,
        validated_records=_validated_records,
    )
    authority_payload = authority.to_payload()
    if (
        len(records) != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
        or type(cache["schema_id"]) is not str
        or cache["schema_id"] != ACOUSTIC_FEATURE_CACHE_SCHEMA_ID
        or type(cache["schema_version"]) is not int
        or cache["schema_version"] != 1
        or type(cache["partition_role"]) is not str
        or cache["partition_role"] != role
        or cache["configuration_sha256"]
        != authority_payload["configuration_sha256"]
        or cache["environment_lock_sha256"] != environment_lock_sha256
        or cache["feature_schema_sha256"] != feature_schema_sha256
        or cache["split_schema_sha256"] != split_schema_sha256
        or cache["split_manifest_sha256"]
        != authority_payload["split_manifest_sha256"]
        or cache["assignment_sha256"] != authority_payload["assignment_sha256"]
        or cache["partition_authority_sha256"]
        != authority_payload["partition_authority_sha256"]
        or cache["tracked_public_authority_commitment_sha256"]
        != tracked_public_authority_commitment_sha256
        or cache["upstream_acoustic_source_commitment_sha256"]
        != _acoustic_source_commitment(role, records)
        or type(cache["feature_names"]) is not list
        or any(type(name) is not str for name in cache["feature_names"])
        or tuple(cache["feature_names"]) != tuple(FEATURE_NAMES)
        or type(cache["records"]) is not list
        or len(cache["records"]) != len(records)
        or cache["self_sha256"] != canonical_payload_sha256(cache)
    ):
        raise PublicMaterialPrerequisiteError(
            "feature cache authority or commitment does not match"
        )
    for name, digest in (
        ("feature cache configuration", cache["configuration_sha256"]),
        ("feature cache environment", cache["environment_lock_sha256"]),
        ("feature cache feature schema", cache["feature_schema_sha256"]),
        ("feature cache split schema", cache["split_schema_sha256"]),
        ("feature cache split manifest", cache["split_manifest_sha256"]),
        ("feature cache assignment", cache["assignment_sha256"]),
        ("feature cache authority", cache["partition_authority_sha256"]),
        (
            "feature cache tracked authority",
            cache["tracked_public_authority_commitment_sha256"],
        ),
        (
            "feature cache acoustic source",
            cache["upstream_acoustic_source_commitment_sha256"],
        ),
        ("feature cache self", cache["self_sha256"]),
    ):
        _require_sha256(digest, name)
    seen: set[str] = set()
    for cached, authoritative in zip(cache["records"], records, strict=True):
        if (
            not _has_exact_string_keys(
                cached,
                set(_FEATURE_CACHE_RECORD_KEYS),
            )
            or tuple(cached) != _FEATURE_CACHE_RECORD_KEYS
            or type(cached["clip_stem"]) is not str
            or cached["clip_stem"] in seen
            or cached["clip_stem"] != authoritative.label_record.clip_stem
            or cached["audio_sha256"] != authoritative.audio_sha256
            or type(cached["audio_size_bytes"]) is not int
            or cached["audio_size_bytes"] <= 0
            or cached["audio_size_bytes"] != authoritative.audio_size_bytes
        ):
            raise PublicMaterialPrerequisiteError(
                "feature cache record authority does not match"
            )
        _require_sha256(cached["audio_sha256"], "feature cache audio identity")
        _exact_feature_values(cached["features"])
        seen.add(cached["clip_stem"])
    return cache


def _build_frozen_diagnostic_slice_mapping(
    *,
    training_authority: Any,
    training_feature_cache: Mapping[str, Any],
    diagnostic_authority: Any,
    diagnostic_feature_cache: Mapping[str, Any],
    _validated_training_records: tuple[Any, ...] | None = None,
    _validated_diagnostic_records: tuple[Any, ...] | None = None,
    _feature_caches_are_validated: bool = False,
) -> dict[str, list[str]]:
    import numpy as np

    from scripts.emotion_state_phase_b_evaluation import (
        validated_partition_records,
    )

    if type(_feature_caches_are_validated) is not bool:
        raise PublicMaterialPrerequisiteError(
            "feature-cache validation state must be an exact boolean"
        )
    tracked_commitment = training_feature_cache[
        "tracked_public_authority_commitment_sha256"
    ]
    if _feature_caches_are_validated:
        if (
            type(training_feature_cache) is not dict
            or type(diagnostic_feature_cache) is not dict
            or _validated_training_records is None
            or _validated_diagnostic_records is None
        ):
            raise PublicMaterialPrerequisiteError(
                "validated slice inputs are incomplete"
            )
        training = training_feature_cache
        diagnostic = diagnostic_feature_cache
    else:
        training = _validate_acoustic_feature_cache(
            training_feature_cache,
            role="training_discovery",
            authority=training_authority,
            tracked_public_authority_commitment_sha256=tracked_commitment,
            environment_lock_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "environment_lock_sha256"
            ],
            feature_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "feature_schema_sha256"
            ],
            split_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "split_schema_sha256"
            ],
        )
        diagnostic = _validate_acoustic_feature_cache(
            diagnostic_feature_cache,
            role="balanced_diagnostic",
            authority=diagnostic_authority,
            tracked_public_authority_commitment_sha256=tracked_commitment,
            environment_lock_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "environment_lock_sha256"
            ],
            feature_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "feature_schema_sha256"
            ],
            split_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "split_schema_sha256"
            ],
        )
    if (
        diagnostic["tracked_public_authority_commitment_sha256"]
        != tracked_commitment
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic and training cache authority commitments differ"
        )
    training_records = (
        validated_partition_records(
            training_authority,
            role="training_discovery",
        )
        if _validated_training_records is None
        else _validated_training_records
    )
    diagnostic_records = (
        validated_partition_records(
            diagnostic_authority,
            role="balanced_diagnostic",
        )
        if _validated_diagnostic_records is None
        else _validated_diagnostic_records
    )
    if (
        type(training_records) is not tuple
        or len(training_records)
        != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS["training_discovery"]
        or type(diagnostic_records) is not tuple
        or len(diagnostic_records)
        != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS["balanced_diagnostic"]
    ):
        raise PublicMaterialPrerequisiteError(
            "validated slice record counts do not match production algebra"
        )
    sentence_ids = tuple(sorted({
        record.label_record.sentence_id
        for record in (*training_records, *diagnostic_records)
    }))
    if len(sentence_ids) != 12:
        raise PublicMaterialPrerequisiteError(
            "frozen diagnostic scenario set must contain exactly 12 IDs"
        )
    names = (
        *(f"source_label:{label}" for label in CLASS_ORDER),
        *(f"scripted_scenario:{sentence}" for sentence in sentence_ids),
        *_VOTE_SLICE_NAMES,
        *_SILENCE_SLICE_NAMES,
    )
    mapping: dict[str, list[str]] = {name: [] for name in names}
    training_silence = np.asarray(
        [
            record["features"]["silence_ratio"]
            for record in training["records"]
        ],
        dtype=np.float64,
    )
    quartiles = tuple(float(value) for value in np.percentile(
        training_silence,
        (25, 50, 75),
        method="linear",
    ))
    for authoritative, cached in zip(
        diagnostic_records,
        diagnostic["records"],
        strict=True,
    ):
        label = authoritative.label_record
        row_id = label.clip_stem
        mapping[f"source_label:{label.label}"].append(row_id)
        mapping[f"scripted_scenario:{label.sentence_id}"].append(row_id)
        if label.vote_agreement < 0.50:
            vote_name = _VOTE_SLICE_NAMES[0]
        elif label.vote_agreement < 0.75:
            vote_name = _VOTE_SLICE_NAMES[1]
        else:
            vote_name = _VOTE_SLICE_NAMES[2]
        mapping[vote_name].append(row_id)
        silence = cached["features"]["silence_ratio"]
        if silence <= quartiles[0]:
            quartile_name = _SILENCE_SLICE_NAMES[0]
        elif silence <= quartiles[1]:
            quartile_name = _SILENCE_SLICE_NAMES[1]
        elif silence <= quartiles[2]:
            quartile_name = _SILENCE_SLICE_NAMES[2]
        else:
            quartile_name = _SILENCE_SLICE_NAMES[3]
        mapping[quartile_name].append(row_id)
    result = dict(sorted(mapping.items()))
    if len(result) != EXPECTED_DIAGNOSTIC_SLICE_COUNT or any(
        sum(len(result[name]) for name in family) != len(diagnostic_records)
        for family in (
            tuple(name for name in result if name.startswith("source_label:")),
            tuple(name for name in result if name.startswith("scripted_scenario:")),
            tuple(name for name in result if name.startswith("vote_agreement:")),
            tuple(name for name in result if name.startswith("silence_ratio:")),
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "frozen diagnostic slice mapping does not partition all records"
        )
    return result


def _select_ami_source_identities(
    authority: TrackedPublicAuthority,
) -> tuple[SourceByteIdentity, ...]:
    direct_families = (
        ("words", f"{_AMI_EXTRACTED_ROOT}words/", ".words.xml"),
        ("segments", f"{_AMI_EXTRACTED_ROOT}segments/", ".segments.xml"),
        (
            "dialogue_acts",
            f"{_AMI_EXTRACTED_ROOT}dialogueActs/",
            ".dialog-act.xml",
        ),
        (
            "adjacency_pairs",
            f"{_AMI_EXTRACTED_ROOT}dialogueActs/",
            ".adjacency-pairs.xml",
        ),
    )

    def direct_family(path: str) -> str | None:
        for family, prefix, suffix in direct_families:
            if not path.startswith(prefix):
                continue
            basename = path[len(prefix):]
            if (
                "/" not in basename
                and basename.endswith(suffix)
                and len(basename) > len(suffix)
            ):
                return family
        return None

    frozen = _exact_tracked_public_authority(authority)
    if frozen.ami_official_order != AMI_FULL_CORPUS_ORDER:
        raise PublicMaterialPrerequisiteError("AMI official order changed")
    official_meetings = frozenset(frozen.ami_official_order)
    selected: list[SourceByteIdentity] = []
    excluded: list[str] = []
    outside_partition_paths: set[str] = set()
    excluded_family_counts = Counter()
    full_family_counts = Counter()
    retained_family_counts = Counter()
    basenames: set[str] = set()
    paths: set[str] = set()
    for identity in frozen.ami_files:
        path = _validate_lexical_project_path(
            identity.project_relative_path,
            "AMI source identity",
        )
        if not path.startswith(_AMI_ROOT):
            raise PublicMaterialPrerequisiteError(
                "AMI source identity is outside the frozen AMI root"
            )
        if path in paths:
            raise PublicMaterialPrerequisiteError(
                "AMI source identity path is duplicated"
            )
        paths.add(path)
        _require_sha256(identity.sha256, "AMI source identity")
        if type(identity.size_bytes) is not int or identity.size_bytes <= 0:
            raise PublicMaterialPrerequisiteError(
                "AMI source identity size must be a positive integer"
            )
        if path == _AMI_MEETING_UNIVERSE_PATH:
            family = "meetings"
        elif path == _AMI_PARTICIPANTS_PATH:
            family = "participants"
        else:
            family = direct_family(path)
        if family is None and path in _AMI_EXCLUDED_SOURCE_PATHS:
            excluded.append(path)
            continue
        if family is None:
            raise PublicMaterialPrerequisiteError(
                "AMI source identity is not an exact frozen source path"
            )
        if family in {"words", "segments", "dialogue_acts", "adjacency_pairs"}:
            filename = path.rsplit("/", 1)[-1]
            match = (
                _AMI_ADJACENCY_FILENAME.fullmatch(filename)
                if family == "adjacency_pairs"
                else _AMI_PARSER_ANNOTATION_FILENAME.fullmatch(filename)
            )
            expected_annotation_family = (
                None
                if family == "adjacency_pairs"
                else {
                    "words": "words",
                    "segments": "segments",
                    "dialogue_acts": "dialog-act",
                }[family]
            )
            if match is None or (
                family != "adjacency_pairs"
                and match.group("family") != expected_annotation_family
            ):
                raise PublicMaterialPrerequisiteError(
                    "AMI annotation filename is not canonical"
                )
            if path not in AMI_EXPECTED_ANNOTATION_PATHS:
                raise PublicMaterialPrerequisiteError(
                    "AMI annotation path is outside the exact tracked family"
                )
            if family != "adjacency_pairs":
                full_family_counts[family] += 1
            if match.group("meeting") not in official_meetings:
                if path not in _AMI_OUTSIDE_PARTITION_SOURCE_PATHS:
                    raise PublicMaterialPrerequisiteError(
                        "AMI annotation is outside the official partition"
                    )
                outside_partition_paths.add(path)
                continue
        if family == "adjacency_pairs":
            excluded_family_counts[family] += 1
            continue
        basename = path.rsplit("/", 1)[-1]
        if basename in basenames:
            raise PublicMaterialPrerequisiteError(
                "AMI selected source basename collides"
            )
        basenames.add(basename)
        if family in {"meetings", "participants"}:
            full_family_counts[family] += 1
        retained_family_counts[family] += 1
        selected.append(identity)
    if full_family_counts != Counter({
        "meetings": 1,
        "participants": 1,
        "words": 687,
        "segments": 687,
        "dialogue_acts": 556,
    }) or retained_family_counts != Counter({
        "meetings": 1,
        "participants": 1,
        "words": 683,
        "segments": 683,
        "dialogue_acts": 556,
    }) or len(selected) != EXPECTED_AMI_SELECTED_SOURCE_COUNT or (
        len(excluded) != 3
        or set(excluded) != set(_AMI_EXCLUDED_SOURCE_PATHS)
    ) or outside_partition_paths != _AMI_OUTSIDE_PARTITION_SOURCE_PATHS or (
        excluded_family_counts != Counter({"adjacency_pairs": 139})
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI selected source families do not match the official partition"
        )
    return tuple(selected)


def _ami_source_authority_sha256(
    selected: Sequence[SourceByteIdentity],
) -> str:
    return _canonical_digest({
        "schema_id": "emotion-state-phase-b-ami-selected-source-authority-v1",
        "files": [
            {
                "project_relative_path": item.project_relative_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
            }
            for item in selected
        ],
    })


def _serialize_ami_meeting(meeting: Any) -> dict[str, Any]:
    from scripts.emotion_state_phase_b_ami_mechanics import (
        _validated_ami_meeting_evidence_v2,
    )

    validated = _validated_ami_meeting_evidence_v2(meeting)

    def turn_payload(turn: Any, *, dialogue: bool) -> dict[str, Any]:
        payload = {
            "meeting_id": turn.meeting_id,
            "participant_id": turn.participant_id,
            "start_ms": turn.start_ms,
            "end_ms": turn.end_ms,
        }
        if dialogue:
            payload["dialogue_act"] = turn.dialogue_act
        return payload

    return {
        "meeting_id": validated.meeting_id,
        "participants": list(validated.participants),
        "timing_file_present": validated.timing_file_present,
        "timed_turns": (
            None
            if validated.timed_turns is None
            else [turn_payload(turn, dialogue=False) for turn in validated.timed_turns]
        ),
        "dialogue_turns": (
            None
            if validated.dialogue_turns is None
            else [
                turn_payload(turn, dialogue=True)
                for turn in validated.dialogue_turns
            ]
        ),
        "dialogue_act_file_count": validated.dialogue_act_file_count,
        "fully_labeled_dialogue_act_file_count": (
            validated.fully_labeled_dialogue_act_file_count
        ),
        "unlabeled_dialogue_act_record_count": (
            validated.unlabeled_dialogue_act_record_count
        ),
        "unlabeled_dialogue_act_file_count": (
            validated.unlabeled_dialogue_act_file_count
        ),
    }


def _restore_ami_meetings(value: Any) -> tuple[Any, ...]:
    from scripts.emotion_state_phase_b_ami_mechanics import (
        AmiMeetingEvidenceV2,
        TimedTurn,
        Turn,
    )
    from scripts.validate_emotion_state_002_phase_b import (
        _ami_v2_serialized_meetings,
    )

    if type(value) is not list:
        raise PublicMaterialPrerequisiteError(
            "AMI evidence meetings must be a list"
        )
    try:
        validated = _ami_v2_serialized_meetings(value)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"AMI evidence meeting projection is invalid: {error}"
        ) from error
    meetings = []
    for meeting in validated:
        timed = meeting["timed_turns"]
        dialogue = meeting["dialogue_turns"]
        meetings.append(AmiMeetingEvidenceV2(
            meeting_id=meeting["meeting_id"],
            participants=tuple(meeting["participants"]),
            timing_file_present=meeting["timing_file_present"],
            timed_turns=(
                None
                if timed is None
                else tuple(TimedTurn(**turn) for turn in timed)
            ),
            dialogue_turns=(
                None
                if dialogue is None
                else tuple(Turn(**turn) for turn in dialogue)
            ),
            dialogue_act_file_count=meeting["dialogue_act_file_count"],
            fully_labeled_dialogue_act_file_count=(
                meeting["fully_labeled_dialogue_act_file_count"]
            ),
            unlabeled_dialogue_act_record_count=(
                meeting["unlabeled_dialogue_act_record_count"]
            ),
            unlabeled_dialogue_act_file_count=(
                meeting["unlabeled_dialogue_act_file_count"]
            ),
        ))
    return tuple(meetings)


def _build_ami_evidence_cache(
    *,
    tracked_authority: TrackedPublicAuthority,
    meetings: Sequence[Any],
    aggregate: Mapping[str, Any],
    tracked_public_authority_commitment_sha256: str,
) -> dict[str, Any]:
    if type(aggregate) is not dict:
        raise PublicMaterialPrerequisiteError(
            "AMI aggregate must be an exact mapping"
        )
    selected = _select_ami_source_identities(tracked_authority)
    if isinstance(meetings, (str, bytes)) or not isinstance(meetings, Sequence):
        raise PublicMaterialPrerequisiteError("AMI meeting evidence must be a sequence")
    meeting_tuple = tuple(meetings)
    membership = tuple(tracked_authority.ami_partition_membership)
    official_order = tuple(tracked_authority.ami_official_order)
    if tuple(meeting.meeting_id for meeting in meeting_tuple) != official_order:
        raise PublicMaterialPrerequisiteError(
            "AMI meeting evidence does not match official order"
        )
    tracked_commitment = _require_sha256(
        tracked_public_authority_commitment_sha256,
        "AMI tracked public authority commitment",
    )
    serialized = [_serialize_ami_meeting(meeting) for meeting in meeting_tuple]
    payload: dict[str, Any] = {
        "schema_id": AMI_EVIDENCE_CACHE_SCHEMA_ID,
        "schema_version": 1,
        "source_authority_sha256": _ami_source_authority_sha256(selected),
        "tracked_public_authority_commitment_sha256": tracked_commitment,
        "source_file_count": EXPECTED_AMI_SELECTED_SOURCE_COUNT,
        "meetings": serialized,
        "partition_membership": [
            [name, list(identifiers)] for name, identifiers in membership
        ],
        "official_order": list(official_order),
        "aggregate": copy.deepcopy(dict(aggregate)),
    }
    payload["aggregate_sha256"] = _canonical_digest(payload["aggregate"])
    payload["self_sha256"] = canonical_payload_sha256(payload)
    return _validate_ami_evidence_cache(
        payload,
        tracked_authority=tracked_authority,
        tracked_public_authority_commitment_sha256=tracked_commitment,
    )


def _validate_ami_evidence_cache(
    payload: Any,
    *,
    tracked_authority: TrackedPublicAuthority,
    tracked_public_authority_commitment_sha256: str,
) -> dict[str, Any]:
    from scripts.emotion_state_phase_b_ami_mechanics import (
        contribution_limited_aggregates_v2,
    )

    if (
        not _has_exact_string_keys(payload, set(_AMI_EVIDENCE_CACHE_KEYS))
        or tuple(payload) != _AMI_EVIDENCE_CACHE_KEYS
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence cache fields do not match"
        )
    cache = copy.deepcopy(payload)
    authority = _exact_tracked_public_authority(tracked_authority)
    selected = _select_ami_source_identities(authority)
    expected_membership = [
        [name, list(identifiers)]
        for name, identifiers in authority.ami_partition_membership
    ]

    def exact_membership(value: Any) -> bool:
        if type(value) is not list or len(value) != len(expected_membership):
            return False
        for actual, expected in zip(value, expected_membership, strict=True):
            if (
                type(actual) is not list
                or len(actual) != 2
                or type(actual[0]) is not str
                or type(actual[1]) is not list
                or any(type(item) is not str for item in actual[1])
                or actual != expected
            ):
                return False
        return True

    official_order = cache["official_order"]
    if (
        type(cache["schema_id"]) is not str
        or cache["schema_id"] != AMI_EVIDENCE_CACHE_SCHEMA_ID
        or type(cache["schema_version"]) is not int
        or cache["schema_version"] != 1
        or cache["source_authority_sha256"]
        != _ami_source_authority_sha256(selected)
        or cache["tracked_public_authority_commitment_sha256"]
        != tracked_public_authority_commitment_sha256
        or type(cache["source_file_count"]) is not int
        or cache["source_file_count"] != EXPECTED_AMI_SELECTED_SOURCE_COUNT
        or not exact_membership(cache["partition_membership"])
        or type(official_order) is not list
        or any(type(item) is not str for item in official_order)
        or official_order != list(authority.ami_official_order)
        or cache["aggregate_sha256"] != _canonical_digest(cache["aggregate"])
        or cache["self_sha256"] != canonical_payload_sha256(cache)
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence cache authority or commitment does not match"
        )
    for name in (
        "source_authority_sha256",
        "tracked_public_authority_commitment_sha256",
        "aggregate_sha256",
        "self_sha256",
    ):
        _require_sha256(cache[name], f"AMI evidence cache {name}")
    meetings = _restore_ami_meetings(cache["meetings"])
    if tuple(meeting.meeting_id for meeting in meetings) != tuple(
        authority.ami_official_order
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence meeting order does not match authority"
        )
    membership = {
        name: tuple(identifiers)
        for name, identifiers in authority.ami_partition_membership
    }
    try:
        rebuilt = contribution_limited_aggregates_v2(
            meetings,
            membership,
            authority.ami_official_order,
            minimum_contributors=MINIMUM_UNIQUE_ACTORS,
        )
        validate_ami_mechanics_aggregates_v2(
            cache["aggregate"],
            meetings=cache["meetings"],
            partition_membership=membership,
            official_order=authority.ami_official_order,
            minimum_contributors=MINIMUM_UNIQUE_ACTORS,
        )
        validate_published_ami_aggregate_v2(cache["aggregate"])
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"AMI evidence aggregate validation failed: {error}"
        ) from error
    if not _matches_packet_contract_exactly(cache["aggregate"], rebuilt):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence aggregate does not replay from meetings"
        )
    return cache


def _validate_slice_analysis_v2(
    payload: Any,
    *,
    diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    if not _has_exact_string_keys(payload, _SLICE_ANALYSIS_KEYS):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice analysis fields do not match"
        )
    sliced = copy.deepcopy(payload)
    if (
        type(sliced["schema_id"]) is not str
        or sliced["schema_id"] != SLICE_ANALYSIS_SCHEMA_ID
        or type(sliced["partition_role"]) is not str
        or sliced["partition_role"] != "balanced_diagnostic"
        or type(sliced["class_order"]) is not list
        or any(type(label) is not str for label in sliced["class_order"])
        or tuple(sliced["class_order"]) != tuple(CLASS_ORDER)
        or type(sliced["instability_tolerance"]) is not float
        or sliced["instability_tolerance"] != 0.10
        or type(sliced["eligible_slice_reversal"]) is not bool
        or type(sliced["eligible_slice_instability"]) is not bool
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice analysis contract does not match"
        )
    try:
        validate_provenance_payload(
            sliced["provenance"],
            expected_role="balanced_diagnostic",
        )
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"diagnostic slice provenance is invalid: {error}"
        ) from error
    if not _matches_packet_contract_exactly(
        sliced["provenance"],
        diagnostic["provenance"],
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice provenance does not match diagnostic"
        )
    for key in (
        "probability_evidence_mint_sha256",
        "evaluation_evidence_mint_sha256",
        "self_sha256",
    ):
        _require_sha256(sliced[key], f"diagnostic slice {key}")
    if (
        sliced["probability_evidence_mint_sha256"]
        != diagnostic["probability_evidence_mint_sha256"]
        or sliced["evaluation_evidence_mint_sha256"]
        != _canonical_digest(diagnostic)
        or sliced["self_sha256"] != canonical_payload_sha256(sliced)
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice lineage or self commitment changed"
        )
    cells = sliced["slices"]
    if (
        type(cells) is not dict
        or any(type(name) is not str for name in cells)
        or tuple(cells) != tuple(sorted(cells))
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice names must be an ordered mapping"
        )
    names = tuple(cells)
    source_labels = tuple(
        name for name in names if name.startswith("source_label:")
    )
    scenarios = tuple(
        name for name in names if name.startswith("scripted_scenario:")
    )
    vote_names = tuple(name for name in names if name.startswith("vote_agreement:"))
    silence_names = tuple(name for name in names if name.startswith("silence_ratio:"))
    expected_source_labels = tuple(
        sorted(f"source_label:{label}" for label in CLASS_ORDER)
    )
    if (
        len(names) != EXPECTED_DIAGNOSTIC_SLICE_COUNT
        or source_labels != expected_source_labels
        or len(scenarios) != 12
        or any(
            re.fullmatch(r"scripted_scenario:[A-Z0-9]{3}", name) is None
            for name in scenarios
        )
        or vote_names != tuple(sorted(_VOTE_SLICE_NAMES))
        or silence_names != tuple(sorted(_SILENCE_SLICE_NAMES))
        or set(names) != set(
            (*source_labels, *scenarios, *vote_names, *silence_names)
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice families do not match the frozen 25 cells"
        )
    diagnostic_cases = diagnostic["provenance"]["case_count"]
    diagnostic_actors = diagnostic["provenance"]["unique_actor_count"]
    full_lifts = {
        baseline: (
            diagnostic["models"]["acoustic"]["macro_f1"]
            - diagnostic["models"][baseline]["macro_f1"]
        )
        for baseline in ("class_prior", "sentence_id")
    }
    derived_reversal = False
    derived_instability = False
    for name, raw_cell in cells.items():
        if not _has_exact_string_keys(raw_cell, _SLICE_CELL_KEYS):
            raise PublicMaterialPrerequisiteError(
                f"diagnostic slice cell fields do not match: {name}"
            )
        cell = raw_cell
        case_count = cell["case_count"]
        actor_count = cell["unique_actor_count"]
        suppressed = cell["suppressed"]
        if (
            type(case_count) is not int
            or not 0 <= case_count <= diagnostic_cases
            or type(actor_count) is not int
            or not 0 <= actor_count <= min(case_count, diagnostic_actors)
            or type(suppressed) is not bool
            or suppressed is not (actor_count < MINIMUM_UNIQUE_ACTORS)
        ):
            raise PublicMaterialPrerequisiteError(
                f"diagnostic slice count or suppression contradicts: {name}"
            )
        for key in (
            "contributor_row_commitment_sha256",
            "contributor_actor_commitment_sha256",
        ):
            _require_sha256(cell[key], f"diagnostic slice {name} {key}")
        if suppressed:
            if (
                cell["model_macro_f1"] is not None
                or cell["paired_macro_f1_lift"] is not None
            ):
                raise PublicMaterialPrerequisiteError(
                    f"suppressed diagnostic slice metrics must be null: {name}"
                )
            continue
        scores = cell["model_macro_f1"]
        lifts = cell["paired_macro_f1_lift"]
        if (
            not _has_exact_string_keys(scores, set(MODEL_KEYS))
            or not _has_exact_string_keys(
                lifts,
                {"class_prior", "sentence_id"},
            )
        ):
            raise PublicMaterialPrerequisiteError(
                f"diagnostic slice metrics do not match: {name}"
            )
        for model, value in scores.items():
            if type(value) is not float or not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise PublicMaterialPrerequisiteError(
                    f"diagnostic slice model metric is invalid: {name}/{model}"
                )
        for baseline, value in lifts.items():
            expected = scores["acoustic"] - scores[baseline]
            if (
                type(value) is not float
                or not math.isfinite(value)
                or not -1.0 <= value <= 1.0
                or not math.isclose(value, expected, rel_tol=0.0, abs_tol=1e-15)
            ):
                raise PublicMaterialPrerequisiteError(
                    f"diagnostic slice lift is invalid: {name}/{baseline}"
                )
            derived_reversal = derived_reversal or value < 0.0
            derived_instability = derived_instability or (
                abs(value - full_lifts[baseline]) > 0.10
            )
    for family in (source_labels, scenarios, vote_names, silence_names):
        if sum(cells[name]["case_count"] for name in family) != diagnostic_cases:
            raise PublicMaterialPrerequisiteError(
                "diagnostic slice family case counts do not cover the diagnostic set"
            )
    if (
        sliced["eligible_slice_reversal"] is not derived_reversal
        or sliced["eligible_slice_instability"] is not derived_instability
    ):
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice derived flags do not match unsuppressed cells"
        )
    validate_aggregate_privacy(sliced)
    return sliced


def build_non_lockbox_review_packet(
    *,
    diagnostic_aggregate: Mapping[str, Any],
    diagnostic_slice_analysis: Mapping[str, Any],
    ami_aggregate: Mapping[str, Any],
    artifact_cache_commitments: Mapping[str, str],
    split_manifest_sha256: str,
    tracked_public_authority_commitment_sha256: str,
) -> dict[str, Any]:
    if (
        type(diagnostic_aggregate) is not dict
        or type(diagnostic_slice_analysis) is not dict
        or type(ami_aggregate) is not dict
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox packet inputs must be exact mappings"
        )
    split_manifest_sha256 = _require_sha256(
        split_manifest_sha256,
        "split manifest identity",
    )
    diagnostic = copy.deepcopy(dict(diagnostic_aggregate))
    sliced = copy.deepcopy(dict(diagnostic_slice_analysis))
    ami = copy.deepcopy(dict(ami_aggregate))
    if (
        type(artifact_cache_commitments) is not dict
        or any(
            type(role) is not str
            for role in artifact_cache_commitments
        )
        or tuple(artifact_cache_commitments) != ARTIFACT_CACHE_COMMITMENT_ORDER
    ):
        raise PublicMaterialPrerequisiteError(
            "artifact cache commitment order does not match"
        )
    cache_commitments = copy.deepcopy(artifact_cache_commitments)
    for role, digest in cache_commitments.items():
        _require_sha256(digest, f"artifact cache commitment {role}")
    tracked_commitment = _require_sha256(
        tracked_public_authority_commitment_sha256,
        "tracked public authority commitment",
    )
    try:
        validate_evaluation_result(
            diagnostic,
            expected_role="balanced_diagnostic",
        )
        validate_published_ami_aggregate_v2(ami)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"non-lockbox aggregate validation failed: {error}"
        ) from error
    if diagnostic.get("final_decision_eligible") is not False:
        raise PublicMaterialPrerequisiteError(
            "balanced diagnostic cannot be final-decision eligible"
        )
    _validate_diagnostic_identity_bindings(
        diagnostic,
        configuration_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
            "configuration_sha256"
        ],
        split_manifest_sha256=split_manifest_sha256,
    )
    sliced = _validate_slice_analysis_v2(sliced, diagnostic=diagnostic)
    validate_aggregate_privacy(diagnostic)
    validate_aggregate_privacy(ami)
    packet: dict[str, Any] = {
        "schema_id": NON_LOCKBOX_PACKET_SCHEMA_ID,
        "schema_version": 4,
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
            "cache_reads": 0,
        },
        "final_decision_eligible": False,
        "tracked_public_authority_commitment_sha256": tracked_commitment,
        "diagnostic_aggregate": diagnostic,
        "diagnostic_aggregate_sha256": _canonical_digest(diagnostic),
        "diagnostic_slice_analysis": sliced,
        "diagnostic_slice_analysis_sha256": _canonical_digest(sliced),
        "ami_aggregate": ami,
        "ami_aggregate_sha256": _canonical_digest(ami),
        "artifact_cache_commitments": cache_commitments,
        "artifact_cache_commitments_sha256": _canonical_digest(
            cache_commitments
        ),
    }
    packet["review_sha256"] = _canonical_digest(packet)
    return validate_non_lockbox_review_packet(packet)


def validate_non_lockbox_review_packet(
    payload: Any,
) -> dict[str, Any]:
    if type(payload) is not dict:
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
        "tracked_public_authority_commitment_sha256",
        "diagnostic_aggregate",
        "diagnostic_aggregate_sha256",
        "diagnostic_slice_analysis",
        "diagnostic_slice_analysis_sha256",
        "ami_aggregate",
        "ami_aggregate_sha256",
        "artifact_cache_commitments",
        "artifact_cache_commitments_sha256",
        "review_sha256",
    }
    if not _has_exact_string_keys(packet, expected_keys):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review packet fields do not match"
        )
    if (
        type(packet["schema_id"]) is not str
        or packet["schema_id"] != NON_LOCKBOX_PACKET_SCHEMA_ID
        or packet["schema_version"] != 4
        or type(packet["schema_version"]) is not int
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox review packet schema does not match"
        )
    digest_fields = (
        "configuration_sha256",
        "split_manifest_sha256",
        "tracked_public_authority_commitment_sha256",
        "diagnostic_aggregate_sha256",
        "diagnostic_slice_analysis_sha256",
        "ami_aggregate_sha256",
        "artifact_cache_commitments_sha256",
        "review_sha256",
    )
    for field in digest_fields:
        _require_sha256(packet[field], f"non-lockbox review {field}")
    if packet["configuration_sha256"] != EXPECTED_EVIDENCE_IDENTITY_SHA256[
        "configuration_sha256"
    ]:
        raise PublicMaterialPrerequisiteError(
            "configuration identity does not match"
        )
    if not _matches_packet_contract_exactly(
        packet["model_settings"],
        EXPECTED_CONFIG["model"],
    ):
        raise PublicMaterialPrerequisiteError(
            "model settings do not match the frozen configuration"
        )
    if not _matches_packet_contract_exactly(
        packet["metric_definitions"],
        EXPECTED_METRIC_DEFINITIONS,
    ):
        raise PublicMaterialPrerequisiteError(
            "metric definitions do not match"
        )
    if not _matches_packet_contract_exactly(
        packet["slice_definitions"],
        EXPECTED_SLICE_DEFINITIONS,
    ):
        raise PublicMaterialPrerequisiteError(
            "slice definitions do not match"
        )
    if not _matches_packet_contract_exactly(
        packet["minimum_unique_contributors_per_cell"],
        MINIMUM_UNIQUE_ACTORS,
    ):
        raise PublicMaterialPrerequisiteError(
            "contributor floor does not match"
        )
    expected_lockbox_access = {
        "open_count": 0,
        "label_reads": 0,
        "feature_reads": 0,
        "audio_reads": 0,
        "cache_reads": 0,
    }
    lockbox_access = packet["lockbox_access"]
    if (
        type(lockbox_access) is not dict
        or any(type(key) is not str for key in lockbox_access)
        or set(lockbox_access) != set(expected_lockbox_access)
        or any(
            type(value) is not int or value != 0
            for value in lockbox_access.values()
        )
    ):
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
        validate_published_ami_aggregate_v2(packet["ami_aggregate"])
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"non-lockbox aggregate validation failed: {error}"
        ) from error
    _validate_diagnostic_identity_bindings(
        packet["diagnostic_aggregate"],
        configuration_sha256=packet["configuration_sha256"],
        split_manifest_sha256=packet["split_manifest_sha256"],
    )
    sliced = _validate_slice_analysis_v2(
        packet["diagnostic_slice_analysis"],
        diagnostic=packet["diagnostic_aggregate"],
    )
    if sliced != packet["diagnostic_slice_analysis"]:
        raise PublicMaterialPrerequisiteError(
            "diagnostic slice analysis changed during validation"
        )
    cache_commitments = packet["artifact_cache_commitments"]
    if (
        type(cache_commitments) is not dict
        or any(type(role) is not str for role in cache_commitments)
        or tuple(cache_commitments) != ARTIFACT_CACHE_COMMITMENT_ORDER
    ):
        raise PublicMaterialPrerequisiteError(
            "artifact cache commitment order does not match"
        )
    for role, digest in cache_commitments.items():
        _require_sha256(digest, f"artifact cache commitment {role}")
    validate_aggregate_privacy(packet["diagnostic_aggregate"])
    validate_aggregate_privacy(packet["diagnostic_slice_analysis"])
    validate_aggregate_privacy(packet["ami_aggregate"])
    if (
        _canonical_digest(packet["diagnostic_aggregate"])
        != packet["diagnostic_aggregate_sha256"]
        or _canonical_digest(packet["diagnostic_slice_analysis"])
        != packet["diagnostic_slice_analysis_sha256"]
        or _canonical_digest(packet["ami_aggregate"])
        != packet["ami_aggregate_sha256"]
        or _canonical_digest(cache_commitments)
        != packet["artifact_cache_commitments_sha256"]
    ):
        raise PublicMaterialPrerequisiteError(
            "non-lockbox aggregate commitment changed"
        )
    review_sha256 = packet.pop("review_sha256")
    if (
        _canonical_digest(packet) != review_sha256
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
        _validate_finite_json_tree(payload)
    except (
        RecursionError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        raise PublicMaterialPrerequisiteError(
            f"{label} tracked evidence is invalid"
        ) from error
    if type(payload) is not dict:
        raise PublicMaterialPrerequisiteError(
            f"{label} tracked evidence must be an object"
        )
    return payload


def _validate_finite_json_tree(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object key is not a string")
            _validate_finite_json_tree(item)
        return
    if type(value) is list:
        for item in value:
            _validate_finite_json_tree(item)
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return
    if type(value) not in {str, int, bool, type(None)}:
        raise ValueError("unsupported JSON primitive")


def _require_object(
    value: Any,
    fields: frozenset[str] | set[str],
    label: str,
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(fields):
        raise PublicMaterialPrerequisiteError(f"{label} fields do not match")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if type(value) is not list:
        raise PublicMaterialPrerequisiteError(f"{label} must be a list")
    return value


def _require_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise PublicMaterialPrerequisiteError(
            f"{label} must be a nonempty string"
        )
    return value


def _require_integer(
    value: Any,
    label: str,
    *,
    minimum: int = 0,
) -> int:
    if type(value) is not int or value < minimum:
        raise PublicMaterialPrerequisiteError(
            f"{label} must be an integer of at least {minimum}"
        )
    return value


def _require_sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise PublicMaterialPrerequisiteError(
            f"{label} must be an uppercase SHA-256"
        )
    return value


def _validate_lexical_project_path(value: Any, label: str) -> str:
    path = _require_string(value, label)
    if (
        unicodedata.normalize("NFC", path) != path
        or path.startswith(("/", "\\"))
        or "\\" in path
        or ":" in path
        or "\x00" in path
    ):
        raise PublicMaterialPrerequisiteError(
            f"{label} path is not canonical project-relative POSIX"
        )
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise PublicMaterialPrerequisiteError(
            f"{label} path contains an escape or empty component"
        )
    for part in parts:
        if (
            part.endswith((".", " "))
            or any(
                character in _WINDOWS_INVALID_COMPONENT_CHARACTERS
                or ord(character) < 32
                or ord(character) == 127
                for character in part
            )
            or part.split(".", 1)[0].upper()
            in _WINDOWS_RESERVED_COMPONENTS
        ):
            raise PublicMaterialPrerequisiteError(
                f"{label} path is not Windows-safe"
            )
    if "/".join(parts) != path:
        raise PublicMaterialPrerequisiteError(
            f"{label} path is not normalized"
        )
    return path


def _validate_unique_strings(
    value: Any,
    label: str,
) -> tuple[str, ...]:
    values = _require_list(value, label)
    result = tuple(
        _require_string(item, f"{label} item")
        for item in values
    )
    if len(result) != len(set(result)):
        raise PublicMaterialPrerequisiteError(
            f"{label} contains a duplicate"
        )
    return result


def _identity(row: Mapping[str, Any]) -> SourceByteIdentity:
    return SourceByteIdentity(
        project_relative_path=row["path"],
        sha256=row["sha256"],
        size_bytes=row["size_bytes"],
    )


def _validate_manifest_profile(
    manifest: dict[str, Any],
    *,
    dataset_id: str,
    source_revision: str | None,
) -> None:
    _require_object(manifest, _MANIFEST_FIELDS, f"{dataset_id} manifest")
    try:
        validate_dataset_manifest(manifest)
    except (PublicDatasetContractError, TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} manifest profile does not match: {error}"
        ) from error
    if (
        type(manifest["dataset_id"]) is not str
        or manifest["dataset_id"] != dataset_id
        or type(manifest["manifest_version"]) is not int
        or manifest["manifest_version"] != 2
        or type(manifest["completion_status"]) is not str
        or manifest["completion_status"] != "verified"
        or type(manifest["source_label"]) is not str
        or manifest["source_label"] != "public-only"
        or manifest["source_revision"] != source_revision
        or (
            source_revision is not None
            and type(manifest["source_revision"]) is not str
        )
        or manifest["runtime_influence_allowed"] is not False
    ):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} manifest identity or boundary does not match"
        )


def _validate_manifest_references(
    manifest: Mapping[str, Any],
    *,
    hash_name: str,
    quality_name: str,
    selected_file_count: int,
    selected_byte_count: int,
    excluded_file_count: int,
) -> None:
    local_hashes = manifest["local_file_hashes"]
    hash_reference = manifest["hash_inventory"]
    exclusion_reference = manifest["exclusion_inventory"]
    expected_hash = _EXPECTED_TRACKED_SHA256[hash_name]
    expected_quality = _EXPECTED_TRACKED_SHA256[quality_name]
    if (
        local_hashes["inventory_sha256"] != expected_hash
        or hash_reference["inventory_sha256"] != expected_hash
        or local_hashes["selected_file_count"] != selected_file_count
        or hash_reference["selected_file_count"] != selected_file_count
        or local_hashes["selected_byte_count"] != selected_byte_count
        or hash_reference["selected_byte_count"] != selected_byte_count
        or exclusion_reference["quality_inventory_sha256"]
        != expected_quality
        or exclusion_reference["included_file_count"]
        != selected_file_count
        or exclusion_reference["excluded_file_count"]
        != excluded_file_count
    ):
        raise PublicMaterialPrerequisiteError(
            "manifest inventory identity, count, or total changed"
        )


def _validate_hash_inventory(
    hashes: dict[str, Any],
    *,
    dataset_id: str,
    prefix: str,
    selected_file_count: int,
    selected_byte_count: int,
    crema: bool,
) -> tuple[SourceByteIdentity, ...]:
    _require_object(
        hashes,
        _HASH_INVENTORY_FIELDS,
        f"{dataset_id} hash inventory",
    )
    if (
        type(hashes["dataset_id"]) is not str
        or hashes["dataset_id"] != dataset_id
        or type(hashes["algorithm"]) is not str
        or hashes["algorithm"] != "SHA-256"
        or type(hashes["inventory_version"]) is not int
        or hashes["inventory_version"] != 1
        or type(hashes["ordering"]) is not str
        or hashes["ordering"] != "ordinal-by-normalized-path"
        or type(hashes["path_normalization"]) is not str
        or hashes["path_normalization"]
        != "project-relative-posix-nfc"
        or type(hashes["selected_file_count"]) is not int
        or hashes["selected_file_count"] != selected_file_count
        or type(hashes["selected_byte_count"]) is not int
        or hashes["selected_byte_count"] != selected_byte_count
    ):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} hash inventory header does not match"
        )
    files = _require_list(hashes["files"], f"{dataset_id} files")
    if len(files) != selected_file_count:
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} inventory file count does not match"
        )
    identities: list[SourceByteIdentity] = []
    paths: list[str] = []
    exact_paths: set[str] = set()
    casefold_paths: set[str] = set()
    total_bytes = 0
    crema_audio_count = 0
    crema_metadata: dict[str, tuple[str, int]] = {}
    for row in files:
        expected_fields = (
            {"git_lfs_oid_sha256", "path", "sha256", "size_bytes"}
            if crema
            and type(row) is dict
            and type(row.get("path")) is str
            and row["path"].startswith(_CREMA_AUDIO_ROOT)
            else {"path", "sha256", "size_bytes"}
        )
        _require_object(
            row,
            expected_fields,
            f"{dataset_id} hash row",
        )
        path = _validate_lexical_project_path(
            row["path"],
            f"{dataset_id} inventory",
        )
        if (
            not path.startswith(prefix)
            or path in exact_paths
            or path.casefold() in casefold_paths
        ):
            raise PublicMaterialPrerequisiteError(
                f"{dataset_id} inventory path is duplicate or outside prefix"
            )
        sha256 = _require_sha256(
            row["sha256"],
            f"{dataset_id} file hash",
        )
        size_bytes = _require_integer(
            row["size_bytes"],
            f"{dataset_id} file size",
            minimum=1,
        )
        if crema and path.startswith(_CREMA_AUDIO_ROOT):
            filename = path.removeprefix(_CREMA_AUDIO_ROOT)
            if "/" in filename or _CREMA_FILENAME.fullmatch(filename) is None:
                raise PublicMaterialPrerequisiteError(
                    "CREMA audio path or filename stem does not match"
                )
            lfs_hash = _require_sha256(
                row["git_lfs_oid_sha256"],
                "CREMA Git LFS hash",
            )
            if lfs_hash != sha256:
                raise PublicMaterialPrerequisiteError(
                    "CREMA Git LFS hash does not match selected file hash"
                )
            crema_audio_count += 1
        elif crema:
            crema_metadata[path] = (sha256, size_bytes)
        paths.append(path)
        exact_paths.add(path)
        casefold_paths.add(path.casefold())
        total_bytes += size_bytes
        identities.append(_identity(row))
    if paths != sorted(paths):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} inventory path order changed"
        )
    if (
        total_bytes != selected_byte_count
        or (crema and crema_audio_count != 7441)
        or (crema and crema_metadata != _CREMA_METADATA_IDENTITIES)
    ):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} inventory count, total, or selection changed"
        )
    by_path = {
        identity.project_relative_path: identity
        for identity in identities
    }
    if not crema and (
        by_path.get(_AMI_ARCHIVE_PATH)
        != SourceByteIdentity(
            _AMI_ARCHIVE_PATH,
            EXPECTED_DATASET_EVIDENCE["ami"]["archive_sha256"],
            22887865,
        )
        or by_path.get(_AMI_PARTITION_SOURCE_PATH)
        != SourceByteIdentity(
            _AMI_PARTITION_SOURCE_PATH,
            _AMI_PARTITION_SOURCE_SHA256,
            14560,
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI archive or official partition source identity changed"
        )
    return tuple(identities)


def _validate_crema_pcm_details(
    item: Mapping[str, Any],
) -> None:
    details = _require_object(
        item["details"],
        {
            "dependency_keys",
            "filename_metadata",
            "source_label_evidence",
            "wav_metadata",
        },
        "CREMA PCM details",
    )
    filename = item["path"].removeprefix("AudioWAV/")
    match = _CREMA_FILENAME.fullmatch(filename)
    if match is None or item["selected_file_path"] != f"{_CREMA_ROOT}{item['path']}":
        raise PublicMaterialPrerequisiteError(
            "CREMA quality audio path or stem does not match"
        )
    metadata = _require_object(
        details["filename_metadata"],
        {
            "actor_id",
            "extension",
            "intended_emotion_code",
            "intended_label_role",
            "intended_source_label",
            "intensity_code",
            "sentence_code",
        },
        "CREMA filename metadata",
    )
    expected_metadata = {
        "actor_id": match["actor"],
        "extension": "wav",
        "intended_emotion_code": match["emotion"],
        "intended_label_role": "prompt_metadata_only",
        "intended_source_label": _CREMA_EMOTION_LABELS[match["emotion"]],
        "intensity_code": match["intensity"],
        "sentence_code": match["sentence"],
    }
    if any(
        type(metadata[key]) is not str
        or metadata[key] != expected
        for key, expected in expected_metadata.items()
    ):
        raise PublicMaterialPrerequisiteError(
            "CREMA filename metadata does not match the audio path"
        )
    dependency = _require_object(
        details["dependency_keys"],
        {"scripted_scenario", "source_corpus", "speaker"},
        "CREMA dependency keys",
    )
    if dependency != {
        "scripted_scenario": match["sentence"],
        "source_corpus": _CREMA_DATASET_ID,
        "speaker": match["actor"],
    } or any(type(value) is not str for value in dependency.values()):
        raise PublicMaterialPrerequisiteError(
            "CREMA dependency identity does not match filename metadata"
        )
    source = _require_object(
        details["source_label_evidence"],
        {
            "abstained",
            "agreement",
            "ambiguity_reason",
            "ambiguous",
            "audio_presentation_encodings",
            "normalized_source_label",
            "raw_source_label",
            "source_column",
            "source_file_path",
            "vote_distribution",
        },
        "CREMA source label evidence",
    )
    if (
        type(source["abstained"]) is not bool
        or type(source["ambiguous"]) is not bool
        or type(source["audio_presentation_encodings"]) is not list
        or any(
            type(value) is not str
            for value in source["audio_presentation_encodings"]
        )
        or type(source["vote_distribution"]) is not dict
        or any(
            type(key) is not str
            or type(value) is not int
            or value < 0
            for key, value in source["vote_distribution"].items()
        )
        or source["source_file_path"] != "finishedResponses.csv"
        or type(source["source_file_path"]) is not str
        or any(
            value is not None and type(value) is not str
            for value in (
                source["ambiguity_reason"],
                source["normalized_source_label"],
                source["raw_source_label"],
                source["source_column"],
            )
        )
        or (
            source["agreement"] is not None
            and (
                type(source["agreement"]) is not float
                or not 0.0 <= source["agreement"] <= 1.0
            )
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "CREMA source label evidence schema is invalid"
        )
    wav = _require_object(
        details["wav_metadata"],
        {
            "channel_count",
            "duration_seconds",
            "encoding",
            "frame_count",
            "sample_rate_hz",
            "sample_width_bytes",
        },
        "CREMA WAV metadata",
    )
    for field in (
        "channel_count",
        "frame_count",
        "sample_rate_hz",
        "sample_width_bytes",
    ):
        _require_integer(wav[field], f"CREMA WAV {field}", minimum=1)
    if (
        type(wav["duration_seconds"]) is not float
        or wav["duration_seconds"] <= 0.0
        or type(wav["encoding"]) is not str
        or wav["encoding"] != "PCM"
        or wav["duration_seconds"]
        != wav["frame_count"] / wav["sample_rate_hz"]
    ):
        raise PublicMaterialPrerequisiteError(
            "CREMA WAV metadata is invalid"
        )


def _validate_dependency_details(value: Any, label: str) -> None:
    details = _require_object(
        value,
        {
            "meeting_series",
            "meetings",
            "participants",
            "recording_sites",
            "scenarios",
        },
        label,
    )
    for key in details:
        _validate_unique_strings(details[key], f"{label} {key}")


def _validate_partition_source(
    value: Any,
    *,
    meeting_universe: frozenset[str],
    identities: Mapping[str, SourceByteIdentity],
) -> tuple[str, ...]:
    source = _require_object(
        value,
        {
            "canonical_source_url",
            "meeting_universe_source_file_path",
            "partition_definitions",
            "source_file_path",
            "source_sha256",
        },
        "AMI official partition source",
    )
    if (
        source["canonical_source_url"] != _AMI_PARTITION_SOURCE_URL
        or type(source["canonical_source_url"]) is not str
        or source["meeting_universe_source_file_path"]
        != _AMI_MEETING_UNIVERSE_PATH
        or type(source["meeting_universe_source_file_path"]) is not str
        or source["source_file_path"] != _AMI_PARTITION_SOURCE_PATH
        or type(source["source_file_path"]) is not str
        or source["source_sha256"] != _AMI_PARTITION_SOURCE_SHA256
        or type(source["source_sha256"]) is not str
        or _AMI_MEETING_UNIVERSE_PATH not in identities
        or identities.get(_AMI_PARTITION_SOURCE_PATH)
        != SourceByteIdentity(
            _AMI_PARTITION_SOURCE_PATH,
            _AMI_PARTITION_SOURCE_SHA256,
            14560,
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI official partition source binding changed"
        )
    definitions = _require_list(
        source["partition_definitions"],
        "AMI partition definitions",
    )
    if len(definitions) != 2:
        raise PublicMaterialPrerequisiteError(
            "AMI partition definition count changed"
        )
    expected = (
        ("full-corpus", "full_corpus", AMI_FULL_CORPUS_ORDER),
        (
            "scenario-only",
            "scenario",
            tuple(
                meeting
                for meeting in AMI_FULL_CORPUS_ORDER
                if meeting not in frozenset(AMI_FULL_ONLY_ORDER)
            ),
        ),
    )
    observed: list[tuple[str, ...]] = []
    for definition, (
        partition_id,
        partition_type,
        meeting_ids,
    ) in zip(definitions, expected):
        row = _require_object(
            definition,
            {
                "meeting_ids",
                "partition_id",
                "partition_type",
                "source_file_path",
            },
            "AMI partition definition",
        )
        observed_ids = _validate_unique_strings(
            row["meeting_ids"],
            "AMI partition meeting IDs",
        )
        if (
            type(row["partition_id"]) is not str
            or row["partition_id"] != partition_id
            or type(row["partition_type"]) is not str
            or row["partition_type"] != partition_type
            or type(row["source_file_path"]) is not str
            or row["source_file_path"] != _AMI_PARTITION_SOURCE_PATH
            or observed_ids != meeting_ids
            or not set(observed_ids).issubset(meeting_universe)
        ):
            raise PublicMaterialPrerequisiteError(
                "AMI partition membership or order changed"
            )
        observed.append(observed_ids)
    full_corpus, scenario_only = observed
    if (
        len(full_corpus) != 170
        or len(scenario_only) != 138
        or tuple(
            meeting
            for meeting in full_corpus
            if meeting not in frozenset(scenario_only)
        )
        != AMI_FULL_ONLY_ORDER
        or set(scenario_only) & set(AMI_FULL_ONLY_ORDER)
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI partition algebra changed"
        )
    return scenario_only


def _validate_crema_source_metadata(value: Any) -> None:
    source = _require_object(
        value,
        {
            "advertised_utterance_count_used",
            "official_mismatch_wav_counterparts",
            "selected_encoding",
            "source_label_rows",
        },
        "CREMA source metadata",
    )
    if (
        source["advertised_utterance_count_used"] is not False
        or source["official_mismatch_wav_counterparts"] != []
        or type(source["official_mismatch_wav_counterparts"]) is not list
        or source["selected_encoding"] != "wav"
        or type(source["selected_encoding"]) is not str
        or source["source_label_rows"]
        != "finishedResponses.csv audio-only rows"
        or type(source["source_label_rows"]) is not str
    ):
        raise PublicMaterialPrerequisiteError(
            "CREMA source metadata changed"
        )


def _validate_ami_source_metadata(
    value: Any,
    identities: Mapping[str, SourceByteIdentity],
) -> tuple[tuple[str, ...], frozenset[str], frozenset[str]]:
    source = _require_object(
        value,
        {
            "dependency_keys",
            "meeting_series",
            "meetings",
            "multi_party_applicability",
            "official_partition_definitions",
            "official_partition_definitions_are_source_metadata_only",
            "official_partition_paths",
            "official_partition_source",
            "participants",
            "project_case_assignments",
            "recording_sites",
            "scenarios",
            "source_corpus",
        },
        "AMI source metadata",
    )
    meetings = _validate_unique_strings(
        source["meetings"],
        "AMI source meetings",
    )
    participants = _validate_unique_strings(
        source["participants"],
        "AMI source participants",
    )
    meeting_series = _validate_unique_strings(
        source["meeting_series"],
        "AMI source meeting series",
    )
    recording_sites = _validate_unique_strings(
        source["recording_sites"],
        "AMI source recording sites",
    )
    scenarios = _validate_unique_strings(
        source["scenarios"],
        "AMI source scenarios",
    )
    if (
        len(meetings) != 193
        or len(participants) != 876
        or meeting_series
        or recording_sites
        or scenarios
        or source["multi_party_applicability"] is not True
        or source[
            "official_partition_definitions_are_source_metadata_only"
        ]
        is not True
        or source["official_partition_paths"]
        != [_AMI_PARTITION_SOURCE_PATH]
        or type(source["official_partition_paths"]) is not list
        or source["project_case_assignments"] != []
        or type(source["project_case_assignments"]) is not list
        or source["source_corpus"] != _AMI_DATASET_ID
        or type(source["source_corpus"]) is not str
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI source metadata identity changed"
        )
    dependency = _require_object(
        source["dependency_keys"],
        {
            "call_session",
            "dialogue_dyad",
            "meeting_series",
            "recording_site",
            "scripted_scenario",
            "source_corpus",
            "speaker",
        },
        "AMI source dependency keys",
    )
    if (
        dependency["call_session"] != list(meetings)
        or dependency["speaker"] != list(participants)
        or dependency["meeting_series"] != list(meeting_series)
        or dependency["recording_site"] != list(recording_sites)
        or dependency["scripted_scenario"] != list(scenarios)
        or dependency["source_corpus"] != [_AMI_DATASET_ID]
        or dependency["dialogue_dyad"]
        != "not_applicable_multi_party_meeting"
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI source dependency keys changed"
        )
    scenario_only = _validate_partition_source(
        source["official_partition_source"],
        meeting_universe=frozenset(meetings),
        identities=identities,
    )
    if (
        source["official_partition_definitions"]
        != source["official_partition_source"]["partition_definitions"]
        or type(source["official_partition_definitions"]) is not list
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI partition copies do not match"
        )
    return scenario_only, frozenset(meetings), frozenset(participants)


def _validate_quality_inventory(
    quality: dict[str, Any],
    *,
    dataset_id: str,
    identities: tuple[SourceByteIdentity, ...],
    included_file_count: int,
    excluded_file_count: int,
    expected_classifications: Mapping[
        tuple[str, str],
        tuple[int, str],
    ],
    crema: bool,
) -> tuple[str, ...] | None:
    _require_object(
        quality,
        _QUALITY_FIELDS,
        f"{dataset_id} quality inventory",
    )
    if (
        type(quality["dataset_id"]) is not str
        or quality["dataset_id"] != dataset_id
        or type(quality["quality_inventory_version"]) is not int
        or quality["quality_inventory_version"] != 1
        or type(quality["included_file_count"]) is not int
        or quality["included_file_count"] != included_file_count
        or type(quality["excluded_file_count"]) is not int
        or quality["excluded_file_count"] != excluded_file_count
    ):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} quality inventory counts do not match"
        )
    limitations = _require_list(
        quality["limitations"],
        f"{dataset_id} limitations",
    )
    if any(type(value) is not str or not value for value in limitations):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} limitations schema is invalid"
        )
    identity_by_path = {
        identity.project_relative_path: identity
        for identity in identities
    }
    if crema:
        _validate_crema_source_metadata(quality["source_metadata"])
        scenario_only = None
        meeting_universe = frozenset()
        participant_universe = frozenset()
    else:
        (
            scenario_only,
            meeting_universe,
            participant_universe,
        ) = _validate_ami_source_metadata(
            quality["source_metadata"],
            identity_by_path,
        )
    items = _require_list(quality["items"], f"{dataset_id} quality items")
    if len(items) != included_file_count + excluded_file_count:
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} quality item count does not match"
        )
    item_paths: list[str] = []
    exact_item_paths: set[str] = set()
    casefold_paths: set[str] = set()
    included_paths: list[str] = []
    core_paths: list[str] = []
    classifications: Counter[tuple[str, str]] = Counter()
    official_partition_details: dict[str, Any] | None = None
    for item_value in items:
        item = _require_object(
            item_value,
            _QUALITY_ITEM_FIELDS,
            f"{dataset_id} quality item",
        )
        path = _validate_lexical_project_path(
            item["path"],
            f"{dataset_id} quality item",
        )
        if path in exact_item_paths or path.casefold() in casefold_paths:
            raise PublicMaterialPrerequisiteError(
                f"{dataset_id} quality item path is duplicate"
            )
        item_paths.append(path)
        exact_item_paths.add(path)
        casefold_paths.add(path.casefold())
        disposition = _require_string(
            item["disposition"],
            f"{dataset_id} disposition",
        )
        classification = _require_string(
            item["classification"],
            f"{dataset_id} classification",
        )
        reason = _require_string(
            item["reason"],
            f"{dataset_id} reason",
        )
        contract = expected_classifications.get(
            (disposition, classification)
        )
        if contract is None or reason != contract[1]:
            raise PublicMaterialPrerequisiteError(
                f"{dataset_id} classification or reason changed"
            )
        if not crema and classification not in {
            "downloaded_archive",
            "official_partition_metadata",
        }:
            try:
                classified = classify_ami_member(path)
            except (TypeError, ValueError) as error:
                raise PublicMaterialPrerequisiteError(
                    "AMI quality path classification is invalid"
                ) from error
            if (
                type(classified) is not dict
                or classified
                != {
                    "classification": classification,
                    "selected": disposition == "included",
                    "reason": reason,
                }
            ):
                raise PublicMaterialPrerequisiteError(
                    "AMI quality path classification changed"
                )
        classifications[(disposition, classification)] += 1
        if disposition == "included":
            selected_path = _validate_lexical_project_path(
                item["selected_file_path"],
                f"{dataset_id} selected quality item",
            )
            if selected_path not in identity_by_path:
                raise PublicMaterialPrerequisiteError(
                    f"{dataset_id} included path is absent from hash inventory"
                )
            included_paths.append(selected_path)
        elif item["selected_file_path"] is not None:
            raise PublicMaterialPrerequisiteError(
                f"{dataset_id} excluded item minted a selected path"
            )

        details = item["details"]
        if crema and classification == "crema_pcm_wav":
            _validate_crema_pcm_details(item)
        elif crema and classification == "crema_release_metadata":
            _require_object(details, set(), "CREMA release metadata details")
            if (
                item["selected_file_path"] != f"{_CREMA_ROOT}{path}"
                or item["selected_file_path"]
                not in _CREMA_METADATA_IDENTITIES
            ):
                raise PublicMaterialPrerequisiteError(
                    "CREMA release metadata selection changed"
                )
        elif crema and classification == "crema_wav":
            failure = _require_object(
                details,
                {
                    "filename_metadata",
                    "objective_failure",
                    "objective_failure_confirmed",
                    "official_issue",
                },
                "CREMA known no-audio details",
            )
            filename_metadata = _require_object(
                failure["filename_metadata"],
                {
                    "actor_id",
                    "extension",
                    "intended_emotion_code",
                    "intended_label_role",
                    "intended_source_label",
                    "intensity_code",
                    "sentence_code",
                },
                "CREMA known no-audio filename metadata",
            )
            if (
                path != "AudioWAV/1076_MTI_SAD_XX.wav"
                or filename_metadata
                != {
                    "actor_id": "1076",
                    "extension": "wav",
                    "intended_emotion_code": "SAD",
                    "intended_label_role": "prompt_metadata_only",
                    "intended_source_label": "sad",
                    "intensity_code": "XX",
                    "sentence_code": "MTI",
                }
                or any(
                    type(value) is not str
                    for value in filename_metadata.values()
                )
                or failure["objective_failure"]
                != "objective_wav_validation_failed"
                or failure["objective_failure_confirmed"] is not True
                or failure["official_issue"]
                != (
                    "1076_MTI_SAD_XX.wav_has_an_official_documented_"
                    "no_audio_issue"
                )
                or type(failure["objective_failure"]) is not str
                or type(failure["official_issue"]) is not str
            ):
                raise PublicMaterialPrerequisiteError(
                    "CREMA known no-audio exclusion changed"
                )
        elif crema:
            _require_object(details, set(), "CREMA excluded details")
        elif classification == "downloaded_archive":
            archive = _require_object(
                details,
                {"archive_sha256", "archive_size_bytes"},
                "AMI archive details",
            )
            if (
                path != _AMI_ARCHIVE_PATH
                or item["selected_file_path"] != _AMI_ARCHIVE_PATH
                or archive["archive_sha256"]
                != EXPECTED_DATASET_EVIDENCE["ami"]["archive_sha256"]
                or type(archive["archive_sha256"]) is not str
                or archive["archive_size_bytes"] != 22887865
                or type(archive["archive_size_bytes"]) is not int
            ):
                raise PublicMaterialPrerequisiteError(
                    "AMI archive quality identity changed"
                )
        elif classification == "official_partition_metadata":
            if (
                path != _AMI_PARTITION_SOURCE_PATH
                or item["selected_file_path"] != _AMI_PARTITION_SOURCE_PATH
            ):
                raise PublicMaterialPrerequisiteError(
                    "AMI partition quality path changed"
                )
            _validate_partition_source(
                details,
                meeting_universe=meeting_universe,
                identities=identity_by_path,
            )
            official_partition_details = details
        elif disposition == "included":
            _validate_dependency_details(
                details,
                f"AMI {classification} dependency details",
            )
            if item["selected_file_path"] != f"{_AMI_EXTRACTED_ROOT}{path}":
                raise PublicMaterialPrerequisiteError(
                    "AMI selected annotation path binding changed"
                )
            for key, values in details.items():
                universe = (
                    meeting_universe
                    if key == "meetings"
                    else (
                        participant_universe
                        if key == "participants"
                        else frozenset()
                    )
                )
                if values and (
                    not universe
                    or not set(values).issubset(universe)
                ):
                    raise PublicMaterialPrerequisiteError(
                        "AMI dependency detail is outside its authority"
                    )
            if classification in _AMI_CORE_CLASSIFICATIONS:
                if any(details.values()):
                    raise PublicMaterialPrerequisiteError(
                        "AMI quarantined core dependency unexpectedly resolved"
                    )
                core_paths.append(item["selected_file_path"])
        else:
            _require_object(details, set(), "AMI excluded details")
    if item_paths != sorted(item_paths):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} quality item order changed"
        )
    expected_counts = {
        key: count_reason[0]
        for key, count_reason in expected_classifications.items()
    }
    if dict(classifications) != expected_counts:
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} quality classification counts changed"
        )
    if (
        len(included_paths) != len(set(included_paths))
        or set(included_paths) != set(identity_by_path)
    ):
        raise PublicMaterialPrerequisiteError(
            f"{dataset_id} included quality paths do not match hash inventory"
        )
    quarantine = _require_list(
        quality["dependency_quarantine"],
        f"{dataset_id} dependency quarantine",
    )
    if crema:
        if quarantine:
            raise PublicMaterialPrerequisiteError(
                "CREMA dependency quarantine must be empty"
            )
        return None
    quarantine_paths: list[str] = []
    quarantine_casefold: set[str] = set()
    for row_value in quarantine:
        row = _require_object(
            row_value,
            {"path", "reason"},
            "AMI dependency quarantine row",
        )
        path = _validate_lexical_project_path(
            row["path"],
            "AMI dependency quarantine",
        )
        if (
            type(row["reason"]) is not str
            or row["reason"] != "required_participant_identity_missing"
            or path in quarantine_paths
            or path.casefold() in quarantine_casefold
        ):
            raise PublicMaterialPrerequisiteError(
                "AMI dependency quarantine reason or path changed"
            )
        quarantine_paths.append(path)
        quarantine_casefold.add(path.casefold())
    if (
        len(quarantine_paths) != 2069
        or quarantine_paths != sorted(quarantine_paths)
        or set(quarantine_paths) != set(core_paths)
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI dependency quarantine identity does not match participant "
            "identity gaps"
        )
    if (
        official_partition_details is None
        or official_partition_details
        != quality["source_metadata"]["official_partition_source"]
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI official partition copies do not match"
        )
    return scenario_only


def validate_tracked_public_evidence(
    evidence: Mapping[str, bytes],
) -> TrackedPublicAuthority:
    if type(evidence) is not dict and not isinstance(evidence, Mapping):
        raise PublicMaterialPrerequisiteError(
            "tracked dataset evidence must be a mapping"
        )
    if set(evidence) != set(TRACKED_DATASET_EVIDENCE_FILENAMES):
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

    crema_manifest_name = "crema-d-v1.0-audio-wav.manifest.json"
    crema_hash_name = "crema-d-v1.0-audio-wav.hashes.json"
    crema_quality_name = "crema-d-v1.0-audio-wav.quality.json"
    ami_manifest_name = "ami-manual-annotations-v1.6.2.manifest.json"
    ami_hash_name = "ami-manual-annotations-v1.6.2.hashes.json"
    ami_quality_name = "ami-manual-annotations-v1.6.2.quality.json"

    _validate_manifest_profile(
        parsed[crema_manifest_name],
        dataset_id=_CREMA_DATASET_ID,
        source_revision="f3b8611a309886568dfa957141775b2e05add04a",
    )
    _validate_manifest_profile(
        parsed[ami_manifest_name],
        dataset_id=_AMI_DATASET_ID,
        source_revision=None,
    )
    crema_all = _validate_hash_inventory(
        parsed[crema_hash_name],
        dataset_id=_CREMA_DATASET_ID,
        prefix=_CREMA_ROOT,
        selected_file_count=7446,
        selected_byte_count=628813439,
        crema=True,
    )
    ami_files = _validate_hash_inventory(
        parsed[ami_hash_name],
        dataset_id=_AMI_DATASET_ID,
        prefix=_AMI_ROOT,
        selected_file_count=2074,
        selected_byte_count=180905698,
        crema=False,
    )
    _validate_quality_inventory(
        parsed[crema_quality_name],
        dataset_id=_CREMA_DATASET_ID,
        identities=crema_all,
        included_file_count=7446,
        excluded_file_count=22367,
        expected_classifications=_CREMA_CLASSIFICATIONS,
        crema=True,
    )
    scenario_only = _validate_quality_inventory(
        parsed[ami_quality_name],
        dataset_id=_AMI_DATASET_ID,
        identities=ami_files,
        included_file_count=2074,
        excluded_file_count=3086,
        expected_classifications=_AMI_CLASSIFICATIONS,
        crema=False,
    )
    if scenario_only is None:
        raise PublicMaterialPrerequisiteError(
            "AMI official partition authority is missing"
        )
    _validate_manifest_references(
        parsed[crema_manifest_name],
        hash_name=crema_hash_name,
        quality_name=crema_quality_name,
        selected_file_count=7446,
        selected_byte_count=628813439,
        excluded_file_count=22367,
    )
    _validate_manifest_references(
        parsed[ami_manifest_name],
        hash_name=ami_hash_name,
        quality_name=ami_quality_name,
        selected_file_count=2074,
        selected_byte_count=180905698,
        excluded_file_count=3086,
    )
    crema_by_path = {
        identity.project_relative_path: identity
        for identity in crema_all
    }
    crema_audio = tuple(
        identity
        for identity in crema_all
        if identity.project_relative_path.startswith(_CREMA_AUDIO_ROOT)
    )
    if (
        len(crema_audio) != 7441
        or len(ami_files) != 2074
    ):
        raise PublicMaterialPrerequisiteError(
            "tracked public authority count changed"
        )
    return TrackedPublicAuthority(
        crema_audio=crema_audio,
        crema_finished_responses=crema_by_path[
            f"{_CREMA_ROOT}finishedResponses.csv"
        ],
        crema_summary_table=crema_by_path[
            f"{_CREMA_ROOT}processedResults/summaryTable.csv"
        ],
        ami_files=ami_files,
        ami_partition_membership=(
            ("scenario_only", scenario_only),
            ("full_corpus", AMI_FULL_CORPUS_ORDER),
            ("full_only", AMI_FULL_ONLY_ORDER),
        ),
        ami_official_order=AMI_FULL_CORPUS_ORDER,
    )


def _exact_tracked_public_authority(authority: Any) -> TrackedPublicAuthority:
    if type(authority) is not TrackedPublicAuthority:
        raise PublicMaterialPrerequisiteError(
            "tracked public authority type changed"
        )
    if (
        type(authority.crema_audio) is not tuple
        or len(authority.crema_audio) != 7441
        or type(authority.ami_files) is not tuple
        or len(authority.ami_files) != 2074
        or type(authority.ami_partition_membership) is not tuple
        or type(authority.ami_official_order) is not tuple
        or type(authority.crema_finished_responses) is not SourceByteIdentity
        or type(authority.crema_summary_table) is not SourceByteIdentity
        or any(type(item) is not SourceByteIdentity for item in authority.crema_audio)
        or any(type(item) is not SourceByteIdentity for item in authority.ami_files)
    ):
        raise PublicMaterialPrerequisiteError(
            "tracked public authority cardinality or frozen type changed"
        )
    for index, cell in enumerate(authority.ami_partition_membership):
        if (
            type(cell) is not tuple
            or len(cell) != 2
            or type(cell[0]) is not str
            or type(cell[1]) is not tuple
            or any(type(item) is not str for item in cell[1])
        ):
            raise PublicMaterialPrerequisiteError(
                f"AMI partition authority {index} changed"
            )
    if any(type(item) is not str for item in authority.ami_official_order):
        raise PublicMaterialPrerequisiteError(
            "AMI official order authority changed"
        )
    return authority


def _tracked_evidence_snapshot(
    tracked_evidence: Mapping[str, bytes],
) -> dict[str, bytes]:
    if not isinstance(tracked_evidence, Mapping):
        raise PublicMaterialPrerequisiteError(
            "tracked dataset evidence must be a mapping"
        )
    try:
        keys = set(tracked_evidence)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            "tracked dataset evidence keys are invalid"
        ) from error
    if keys != set(TRACKED_DATASET_EVIDENCE_FILENAMES):
        raise PublicMaterialPrerequisiteError(
            "tracked dataset evidence set does not match"
        )
    snapshot: dict[str, bytes] = {}
    for name in TRACKED_DATASET_EVIDENCE_FILENAMES:
        content = tracked_evidence[name]
        if type(content) is not bytes:
            raise PublicMaterialPrerequisiteError(
                f"{name} tracked evidence must be bytes"
            )
        snapshot[name] = content
    return snapshot


def tracked_public_authority_commitment_sha256(
    *,
    tracked_evidence: Mapping[str, bytes],
    authority: TrackedPublicAuthority,
) -> str:
    evidence_snapshot = _tracked_evidence_snapshot(tracked_evidence)
    validated_authority = _exact_tracked_public_authority(authority)

    def identity_payload(source: SourceByteIdentity) -> dict[str, Any]:
        return {
            "project_relative_path": source.project_relative_path,
            "sha256": source.sha256,
            "size_bytes": source.size_bytes,
        }

    preimage = {
        "schema_id": (
            "emotion-state-phase-b-tracked-public-authority-commitment-v1"
        ),
        "tracked_evidence": [
            {
                "name": name,
                "sha256": hashlib.sha256(
                    evidence_snapshot[name]
                ).hexdigest().upper(),
                "size_bytes": len(evidence_snapshot[name]),
            }
            for name in TRACKED_DATASET_EVIDENCE_FILENAMES
        ],
        "crema_audio": [
            identity_payload(source)
            for source in validated_authority.crema_audio
        ],
        "crema_finished_responses": identity_payload(
            validated_authority.crema_finished_responses
        ),
        "crema_summary_table": identity_payload(
            validated_authority.crema_summary_table
        ),
        "ami_files": [
            identity_payload(source)
            for source in validated_authority.ami_files
        ],
        "ami_partition_membership": [
            [partition_name, list(meeting_ids)]
            for partition_name, meeting_ids
            in validated_authority.ami_partition_membership
        ],
        "ami_official_order": list(validated_authority.ami_official_order),
    }
    return hashlib.sha256(json.dumps(
        preimage,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")).hexdigest().upper()


def build_production_preflight_artifacts(
    *,
    tracked_evidence: Mapping[str, bytes],
    finished_responses: bytes,
    summary_table: bytes,
    configuration: Mapping[str, Any],
) -> ProductionPreflightArtifacts:
    if type(finished_responses) is not bytes:
        raise TypeError("finishedResponses.csv content must be exact bytes")
    if type(summary_table) is not bytes:
        raise TypeError("summaryTable.csv content must be exact bytes")
    if not isinstance(configuration, Mapping):
        raise TypeError("configuration must be a mapping")
    evidence_snapshot = _tracked_evidence_snapshot(tracked_evidence)
    authority = _exact_tracked_public_authority(
        validate_tracked_public_evidence(dict(evidence_snapshot))
    )
    source_commitment = tracked_public_authority_commitment_sha256(
        tracked_evidence=dict(evidence_snapshot),
        authority=authority,
    )
    configuration_copy = copy.deepcopy(dict(configuration))
    validated_configuration = validate_config(configuration_copy)

    finished_identity = authority.crema_finished_responses
    summary_identity = authority.crema_summary_table
    supplied_identities = (
        (finished_responses, finished_identity, "finishedResponses.csv"),
        (summary_table, summary_identity, "summaryTable.csv"),
    )
    for content, expected, name in supplied_identities:
        if (
            len(content) != expected.size_bytes
            or _sha256(content) != expected.sha256
        ):
            raise PublicMaterialPrerequisiteError(
                f"{name} byte identity does not match tracked authority"
            )

    stems: list[str] = []
    source_by_stem: dict[str, SourceByteIdentity] = {}
    for source in authority.crema_audio:
        path = source.project_relative_path
        if (
            type(path) is not str
            or not path.startswith(_CREMA_AUDIO_ROOT)
            or not path.endswith(".wav")
        ):
            raise PublicMaterialPrerequisiteError(
                "CREMA audio authority path changed"
            )
        stem = path[len(_CREMA_AUDIO_ROOT):-4]
        if not stem or "/" in stem or "\\" in stem or stem in source_by_stem:
            raise PublicMaterialPrerequisiteError(
                "CREMA audio authority stem changed"
            )
        stems.append(stem)
        source_by_stem[stem] = source
    if len(stems) != 7441:
        raise PublicMaterialPrerequisiteError(
            "CREMA audio authority count changed"
        )

    from scripts import emotion_state_phase_b_evaluation as evaluation
    from scripts.emotion_state_phase_b_splits import build_actor_split

    required_evaluation_apis = (
        evaluation.load_crema_reference_labels_bytes,
        evaluation.mint_validated_split_assignment,
        evaluation.serialize_partition_authority_caches,
        evaluation.restore_validated_partition_authority_cache,
        evaluation.validated_partition_records,
    )
    if any(not callable(api) for api in required_evaluation_apis):
        raise PublicMaterialPrerequisiteError(
            "accepted Phase B evaluation API is unavailable"
        )
    records, crema_ledger = evaluation.load_crema_reference_labels_bytes(
        finished_responses,
        summary_table,
        tuple(stems),
    )
    validate_crema_label_ledger(crema_ledger, validated_configuration)
    if len(records) != 7441:
        raise PublicMaterialPrerequisiteError(
            "CREMA label record count changed"
        )

    finished_sha256 = _sha256(finished_responses)
    summary_sha256 = _sha256(summary_table)
    source_binding = crema_ledger.get("source_binding")
    if not isinstance(source_binding, dict) or (
        source_binding.get("finished_responses_sha256") != finished_sha256
        or source_binding.get("summary_table_sha256") != summary_sha256
    ):
        raise PublicMaterialPrerequisiteError(
            "CREMA label ledger source binding does not match supplied CSV bytes"
        )
    input_ledger = {
        "schema_version": 1,
        "phase_a": copy.deepcopy(EXPECTED_PHASE_A_BINDING),
        "dataset_evidence": copy.deepcopy(EXPECTED_DATASET_EVIDENCE),
        "raw_csv_sha256": {
            "finishedResponses.csv": finished_sha256,
            "processedResults/summaryTable.csv": summary_sha256,
        },
        "crema_label_ledger": copy.deepcopy(crema_ledger),
    }
    validated_ledger = validate_phase_b_input_ledger(input_ledger)
    if (
        validated_ledger["raw_csv_sha256"] != input_ledger["raw_csv_sha256"]
        or validated_ledger["crema_label_ledger"]["source_binding"]
        != input_ledger["crema_label_ledger"]["source_binding"]
    ):
        raise PublicMaterialPrerequisiteError(
            "validated input ledger lost supplied CSV identity"
        )

    configuration_sha256 = hashlib.sha256(json.dumps(
        validated_configuration,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")).hexdigest().upper()
    if configuration_sha256 != (
        "24E2186A3ACB19817BF87689F09A2F069AC07B5C1D669364D5FC08BC9AD5FA8F"
    ):
        raise PublicMaterialPrerequisiteError(
            "Phase B semantic configuration identity changed"
        )
    seed_digest = configuration_sha256.lower()
    eligible_records = tuple(record for record in records if record.label is not None)
    if len(eligible_records) != 6570:
        raise PublicMaterialPrerequisiteError(
            "eligible CREMA record count changed"
        )
    eligible_stems = {record.clip_stem for record in eligible_records}
    acoustic_sources = {
        stem: source_by_stem[stem]
        for stem in sorted(eligible_stems)
    }
    if set(acoustic_sources) != eligible_stems:
        raise PublicMaterialPrerequisiteError(
            "eligible acoustic authority mapping is incomplete"
        )
    assignment = build_actor_split(eligible_records, seed_digest)
    split_assignment = evaluation.mint_validated_split_assignment(
        eligible_records,
        assignment,
        seed_digest,
        acoustic_sources=acoustic_sources,
    )
    split_manifest = validate_phase_b_split_manifest(
        split_assignment.to_payload()
    )
    caches = evaluation.serialize_partition_authority_caches(split_assignment)
    roles = (
        "training_discovery",
        "calibration",
        "balanced_diagnostic",
    )
    if type(caches) is not dict or tuple(caches) != roles:
        raise PublicMaterialPrerequisiteError(
            "partition authority cache roles changed"
        )
    validated_caches: dict[str, dict[str, Any]] = {}
    for role in roles:
        validated_caches[role] = validate_phase_b_partition_authority_cache(
            caches[role],
            split_manifest,
            expected_role=role,
        )
    return ProductionPreflightArtifacts(
        source_authority_commitment_sha256=source_commitment,
        input_ledger=copy.deepcopy(validated_ledger),
        split_manifest=copy.deepcopy(split_manifest),
        partition_authority_caches=copy.deepcopy(validated_caches),
    )


def _exact_json_mapping(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise PublicMaterialPrerequisiteError(
            f"{label} must be an exact JSON object"
        )
    try:
        _validate_finite_json_tree(value)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"{label} must contain exact built-in JSON values"
        ) from error
    return copy.deepcopy(value)


def _validated_non_lockbox_static_mappings(
    *,
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    candidates = (
        (
            "configuration",
            configuration,
            validate_config,
            EXPECTED_CONFIG,
            "configuration_sha256",
        ),
        (
            "environment lock",
            environment_lock,
            validate_environment_lock,
            EXPECTED_ENVIRONMENT_LOCK,
            "environment_lock_sha256",
        ),
        (
            "feature schema",
            feature_schema,
            validate_feature_schema,
            EXPECTED_FEATURE_SCHEMA,
            "feature_schema_sha256",
        ),
        (
            "split schema",
            split_schema,
            validate_split_schema,
            EXPECTED_SPLIT_SCHEMA,
            "split_schema_sha256",
        ),
    )
    validated: list[dict[str, Any]] = []
    for label, supplied, validator, expected, identity_name in candidates:
        candidate = _exact_json_mapping(supplied, label)
        try:
            checked = validator(candidate)
        except (TypeError, ValueError) as error:
            raise PublicMaterialPrerequisiteError(
                f"{label} does not match the frozen contract: {error}"
            ) from error
        if not _matches_packet_contract_exactly(checked, expected):
            raise PublicMaterialPrerequisiteError(
                f"{label} does not match the frozen contract"
            )
        digest = _canonical_digest(checked)
        if digest != EXPECTED_EVIDENCE_IDENTITY_SHA256[identity_name]:
            raise PublicMaterialPrerequisiteError(
                f"{label} semantic identity changed"
            )
        validated.append(copy.deepcopy(checked))
    try:
        bound_configuration, bound_feature_schema = (
            validate_config_feature_schema_binding(validated[0], validated[2])
        )
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"configuration and feature schema cross-binding failed: {error}"
        ) from error
    validated[0] = bound_configuration
    validated[2] = bound_feature_schema
    return validated[0], validated[1], validated[2], validated[3]


def _validated_production_role_algebra(
    *,
    authorities: Mapping[str, "ValidatedPartitionAuthority"],
    split_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, tuple[Any, ...]]]:
    from scripts.emotion_state_phase_b_evaluation import (
        ValidatedPartitionAuthority,
        validated_partition_records,
    )

    if (
        type(authorities) is not dict
        or any(type(role) is not str for role in authorities)
        or tuple(authorities) != NON_LOCKBOX_ROLE_ORDER
        or len({id(authority) for authority in authorities.values()})
        != len(NON_LOCKBOX_ROLE_ORDER)
        or any(
            type(authority) is not ValidatedPartitionAuthority
            for authority in authorities.values()
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "production authorities must be three distinct exact non-lockbox roles"
        )
    manifest_candidate = _exact_json_mapping(
        split_manifest,
        "validated split manifest",
    )
    try:
        manifest = validate_phase_b_split_manifest(manifest_candidate)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"validated split manifest is invalid: {error}"
        ) from error
    authority_commitments = manifest["partition_authority_sha256"]
    if not _has_exact_string_keys(
        authority_commitments,
        set(NON_LOCKBOX_ROLE_ORDER),
    ):
        raise PublicMaterialPrerequisiteError(
            "split manifest non-lockbox authorities do not match"
        )

    records_by_role: dict[str, tuple[Any, ...]] = {}
    common_configuration: str | None = None
    common_assignment: str | None = None
    for role in NON_LOCKBOX_ROLE_ORDER:
        authority = authorities[role]
        payload = authority.to_payload()
        try:
            _validate_finite_json_tree(payload)
        except (TypeError, ValueError) as error:
            raise PublicMaterialPrerequisiteError(
                f"{role} authority payload contains non-exact values"
            ) from error
        expected_count = EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
        if (
            type(payload) is not dict
            or type(payload.get("partition_role")) is not str
            or payload["partition_role"] != role
            or type(payload.get("eligible_record_count")) is not int
            or payload["eligible_record_count"] != expected_count
            or type(payload.get("eligible_actor_count")) is not int
            or payload.get("split_manifest_sha256")
            != manifest["split_manifest_sha256"]
            or payload.get("partition_authority_sha256")
            != authority_commitments[role]
            or payload.get("configuration_sha256")
            != manifest["configuration_sha256"]
            or payload.get("assignment_sha256")
            != manifest["assignment_sha256"]
        ):
            raise PublicMaterialPrerequisiteError(
                f"{role} authority does not match production role algebra"
            )
        records = validated_partition_records(authority, role=role)
        if type(records) is not tuple or len(records) != expected_count:
            raise PublicMaterialPrerequisiteError(
                f"{role} record count does not match production role algebra"
            )
        records_by_role[role] = records
        common_configuration = common_configuration or payload[
            "configuration_sha256"
        ]
        common_assignment = common_assignment or payload["assignment_sha256"]
        if (
            payload["configuration_sha256"] != common_configuration
            or payload["assignment_sha256"] != common_assignment
        ):
            raise PublicMaterialPrerequisiteError(
                "non-lockbox authorities do not share frozen lineage"
            )

    final_commitment = manifest["final_lockbox_commitment"]
    nonfinal_count = sum(
        EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
        for role in NON_LOCKBOX_ROLE_ORDER
    )
    if (
        type(manifest["eligible_record_count"]) is not int
        or manifest["eligible_record_count"]
        != EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT
        or type(final_commitment["eligible_record_count"]) is not int
        or final_commitment["eligible_record_count"]
        != EXPECTED_PRODUCTION_FINAL_LOCKBOX_RECORD_COUNT
        or type(nonfinal_count) is not int
        or nonfinal_count != EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT
        or type(
            nonfinal_count + final_commitment["eligible_record_count"]
        ) is not int
        or nonfinal_count + final_commitment["eligible_record_count"]
        != EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT
        or sum(len(records) for records in records_by_role.values())
        != EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT
    ):
        raise PublicMaterialPrerequisiteError(
            "production role algebra must be exactly 2491/959/939 plus 2181"
        )
    return copy.deepcopy(manifest), records_by_role


def _selected_nonfinal_audio_sources(
    *,
    tracked_authority: TrackedPublicAuthority,
    records_by_role: Mapping[str, Sequence[Any]],
) -> dict[str, tuple[SourceByteIdentity, ...]]:
    authority = _exact_tracked_public_authority(tracked_authority)
    by_stem: dict[str, SourceByteIdentity] = {}
    paths: set[str] = set()
    for source in authority.crema_audio:
        path = _validate_lexical_project_path(
            source.project_relative_path,
            "CREMA audio source identity",
        )
        _require_sha256(source.sha256, "CREMA audio source identity")
        if (
            type(source.size_bytes) is not int
            or source.size_bytes <= 0
            or not path.startswith(_CREMA_AUDIO_ROOT)
            or not path.endswith(".wav")
            or path in paths
        ):
            raise PublicMaterialPrerequisiteError(
                "CREMA audio source identity does not match frozen authority"
            )
        stem = path[len(_CREMA_AUDIO_ROOT):-4]
        if not stem or "/" in stem or stem in by_stem:
            raise PublicMaterialPrerequisiteError(
                "CREMA audio source stem is duplicated or invalid"
            )
        paths.add(path)
        by_stem[stem] = source
    if len(by_stem) != 7441:
        raise PublicMaterialPrerequisiteError(
            "CREMA audio source authority count changed"
        )

    selected: dict[str, tuple[SourceByteIdentity, ...]] = {}
    consumed: set[str] = set()
    for role in NON_LOCKBOX_ROLE_ORDER:
        role_sources: list[SourceByteIdentity] = []
        for record in records_by_role[role]:
            stem = record.label_record.clip_stem
            source = by_stem.get(stem)
            if (
                source is None
                or source.sha256 != record.audio_sha256
                or source.size_bytes != record.audio_size_bytes
                or stem in consumed
            ):
                raise PublicMaterialPrerequisiteError(
                    f"{role} audio source does not match sealed authority"
                )
            consumed.add(stem)
            role_sources.append(source)
        if len(role_sources) != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]:
            raise PublicMaterialPrerequisiteError(
                f"{role} audio source count changed"
            )
        selected[role] = tuple(role_sources)
    if len(consumed) != EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox audio source count changed"
        )
    return selected


def _validated_non_lockbox_tracked_authority(
    authority: Any,
) -> TrackedPublicAuthority:
    frozen = _exact_tracked_public_authority(authority)
    metadata = (
        (
            frozen.crema_finished_responses,
            f"{_CREMA_ROOT}finishedResponses.csv",
            "CREMA finished-responses source",
        ),
        (
            frozen.crema_summary_table,
            f"{_CREMA_ROOT}processedResults/summaryTable.csv",
            "CREMA summary-table source",
        ),
    )
    for source, expected_path, label in metadata:
        if (
            _validate_lexical_project_path(
                source.project_relative_path,
                label,
            ) != expected_path
            or type(source.size_bytes) is not int
            or source.size_bytes <= 0
        ):
            raise PublicMaterialPrerequisiteError(
                f"{label} identity changed"
            )
        _require_sha256(source.sha256, label)
    scenario_only = tuple(
        meeting
        for meeting in AMI_FULL_CORPUS_ORDER
        if meeting not in set(AMI_FULL_ONLY_ORDER)
    )
    expected_membership = (
        ("scenario_only", scenario_only),
        ("full_corpus", AMI_FULL_CORPUS_ORDER),
        ("full_only", AMI_FULL_ONLY_ORDER),
    )
    if (
        not _matches_packet_contract_exactly(
            frozen.ami_partition_membership,
            expected_membership,
        )
        or not _matches_packet_contract_exactly(
            frozen.ami_official_order,
            AMI_FULL_CORPUS_ORDER,
        )
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI partition authority does not match the frozen release matrix"
        )
    return frozen


def _partition_evidence_from_feature_cache(
    *,
    role: str,
    authority: "ValidatedPartitionAuthority",
    records: Sequence[Any],
    cache: Mapping[str, Any],
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
    model_identity: Mapping[str, Any],
) -> Any:
    import numpy as np

    from scripts.emotion_state_phase_b_evaluation import mint_partition_evidence
    from scripts.emotion_state_phase_b_features import FEATURE_NAMES

    feature_rows = [
        [cached["features"][name] for name in FEATURE_NAMES]
        for cached in cache["records"]
    ]
    return mint_partition_evidence(
        partition_role=role,
        row_ids=tuple(
            record.label_record.clip_stem for record in records
        ),
        actor_ids=tuple(
            record.label_record.actor_id for record in records
        ),
        labels=np.asarray(
            [record.label_record.label for record in records],
            dtype="<U1",
        ),
        sentences=np.asarray(
            [record.label_record.sentence_id for record in records],
            dtype="<U3",
        ),
        features=np.asarray(feature_rows, dtype=np.float64),
        upstream_acoustic_source_commitment_sha256=cache[
            "upstream_acoustic_source_commitment_sha256"
        ],
        split_assignment=authority,
        configuration=configuration,
        environment_lock=environment_lock,
        feature_schema=feature_schema,
        split_schema=split_schema,
        model_identity=model_identity,
    )


def _evaluate_non_lockbox_partition_evidence(
    *,
    partition_evidence: Mapping[str, Any],
    model_seed: int,
    configuration: Mapping[str, Any],
) -> tuple[Any, Any, Any]:
    from scripts.emotion_state_phase_b_evaluation import (
        calibrate_thresholds,
        evaluate_partition,
        fit_frozen_models,
        predict_probabilities,
    )

    fitted = fit_frozen_models(
        partition_evidence["training_discovery"],
        model_seed,
    )
    calibration_probabilities = predict_probabilities(
        fitted,
        partition_evidence["calibration"],
    )
    thresholds = calibrate_thresholds(
        calibration_probabilities,
        tuple(configuration["coverage_targets"]),
    )
    diagnostic_probabilities = predict_probabilities(
        fitted,
        partition_evidence["balanced_diagnostic"],
    )
    diagnostic = evaluate_partition(
        diagnostic_probabilities,
        thresholds,
    )
    return diagnostic_probabilities, diagnostic, thresholds


def _ami_loader_inputs(
    *,
    selected_sources: Sequence[SourceByteIdentity],
    read_verified_ami: Callable[[SourceByteIdentity], bytes],
) -> tuple[Any, tuple[Any, ...], tuple[Any, ...], tuple[Any, ...], Any]:
    from scripts.emotion_state_phase_b_ami_mechanics import AmiXmlBytes

    metadata = None
    participant_metadata = None
    words: list[AmiXmlBytes] = []
    segments: list[AmiXmlBytes] = []
    dialogue_acts: list[AmiXmlBytes] = []
    for source in selected_sources:
        content = read_verified_ami(source)
        if (
            type(content) is not bytes
            or len(content) != source.size_bytes
            or _sha256(content) != source.sha256
        ):
            raise PublicMaterialPrerequisiteError(
                "AMI source bytes do not match sealed identity"
            )
        filename = Path(source.project_relative_path).name
        wrapped = AmiXmlBytes(filename, content)
        path = source.project_relative_path
        if path == _AMI_MEETING_UNIVERSE_PATH:
            if metadata is not None:
                raise PublicMaterialPrerequisiteError(
                    "AMI meetings metadata is duplicated"
                )
            metadata = wrapped
        elif path == _AMI_PARTICIPANTS_PATH:
            if participant_metadata is not None:
                raise PublicMaterialPrerequisiteError(
                    "AMI participant metadata is duplicated"
                )
            participant_metadata = wrapped
        elif path.startswith(f"{_AMI_EXTRACTED_ROOT}words/"):
            words.append(wrapped)
        elif path.startswith(f"{_AMI_EXTRACTED_ROOT}segments/"):
            segments.append(wrapped)
        elif path.startswith(f"{_AMI_EXTRACTED_ROOT}dialogueActs/"):
            dialogue_acts.append(wrapped)
        else:
            raise PublicMaterialPrerequisiteError(
                "AMI selected source was not consumed"
            )
    if (
        metadata is None
        or participant_metadata is None
        or len(words) != 683
        or len(segments) != 683
        or len(dialogue_acts) != 556
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI loader source families do not match frozen counts"
        )
    return (
        metadata,
        tuple(words),
        tuple(segments),
        tuple(dialogue_acts),
        participant_metadata,
    )


def _canonical_artifact_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise PublicMaterialPrerequisiteError(
            "non-lockbox artifact is not canonical JSON"
        ) from error


def _validate_source_silent_ami_evidence_cache(
    payload: Any,
    *,
    tracked_public_authority_commitment_sha256: str,
) -> dict[str, Any]:
    from scripts.emotion_state_phase_b_ami_mechanics import (
        contribution_limited_aggregates_v2,
    )

    if (
        not _has_exact_string_keys(payload, set(_AMI_EVIDENCE_CACHE_KEYS))
        or tuple(payload) != _AMI_EVIDENCE_CACHE_KEYS
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence cache fields do not match"
        )
    cache = _exact_json_mapping(payload, "AMI evidence cache")
    scenario_only = tuple(
        meeting
        for meeting in AMI_FULL_CORPUS_ORDER
        if meeting not in set(AMI_FULL_ONLY_ORDER)
    )
    expected_membership = [
        ["scenario_only", list(scenario_only)],
        ["full_corpus", list(AMI_FULL_CORPUS_ORDER)],
        ["full_only", list(AMI_FULL_ONLY_ORDER)],
    ]
    if (
        type(cache["schema_id"]) is not str
        or cache["schema_id"] != AMI_EVIDENCE_CACHE_SCHEMA_ID
        or type(cache["schema_version"]) is not int
        or cache["schema_version"] != 1
        or type(cache["source_file_count"]) is not int
        or cache["source_file_count"] != EXPECTED_AMI_SELECTED_SOURCE_COUNT
        or not _matches_packet_contract_exactly(
            cache["partition_membership"],
            expected_membership,
        )
        or not _matches_packet_contract_exactly(
            cache["official_order"],
            list(AMI_FULL_CORPUS_ORDER),
        )
        or cache["tracked_public_authority_commitment_sha256"]
        != tracked_public_authority_commitment_sha256
        or cache["aggregate_sha256"] != _canonical_digest(cache["aggregate"])
        or cache["self_sha256"] != canonical_payload_sha256(cache)
    ):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence cache authority or commitment does not match"
        )
    for name in (
        "source_authority_sha256",
        "tracked_public_authority_commitment_sha256",
        "aggregate_sha256",
        "self_sha256",
    ):
        _require_sha256(cache[name], f"AMI evidence cache {name}")
    meetings = _restore_ami_meetings(cache["meetings"])
    if tuple(meeting.meeting_id for meeting in meetings) != AMI_FULL_CORPUS_ORDER:
        raise PublicMaterialPrerequisiteError(
            "AMI evidence meeting order does not match authority"
        )
    membership = {
        name: tuple(identifiers)
        for name, identifiers in expected_membership
    }
    try:
        rebuilt = contribution_limited_aggregates_v2(
            meetings,
            membership,
            AMI_FULL_CORPUS_ORDER,
            minimum_contributors=MINIMUM_UNIQUE_ACTORS,
        )
        validate_ami_mechanics_aggregates_v2(
            cache["aggregate"],
            meetings=cache["meetings"],
            partition_membership=membership,
            official_order=AMI_FULL_CORPUS_ORDER,
            minimum_contributors=MINIMUM_UNIQUE_ACTORS,
        )
        validate_published_ami_aggregate_v2(cache["aggregate"])
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"AMI evidence aggregate validation failed: {error}"
        ) from error
    if not _matches_packet_contract_exactly(cache["aggregate"], rebuilt):
        raise PublicMaterialPrerequisiteError(
            "AMI evidence aggregate does not replay from meetings"
        )
    return cache


def _artifact_cache_commitments(
    *,
    feature_caches: Mapping[str, Mapping[str, Any]],
    ami_evidence: Mapping[str, Any],
) -> dict[str, str]:
    return {
        **{
            role: feature_caches[role]["self_sha256"]
            for role in NON_LOCKBOX_ROLE_ORDER
        },
        "ami_evidence": ami_evidence["self_sha256"],
    }


def build_production_non_lockbox_artifacts(
    *,
    authorities: Mapping[str, "ValidatedPartitionAuthority"],
    split_manifest: Mapping[str, Any],
    read_verified_audio: Callable[[SourceByteIdentity], bytes],
    read_verified_ami: Callable[[SourceByteIdentity], bytes],
    tracked_evidence: Mapping[str, bytes],
    tracked_authority: TrackedPublicAuthority,
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
) -> ProductionNonLockboxArtifacts:
    from scripts.emotion_state_phase_b_ami_mechanics import (
        contribution_limited_aggregates_v2,
        load_ami_meeting_evidence_v2,
    )
    from scripts.emotion_state_phase_b_evaluation import (
        frozen_model_identity,
        mint_slice_analysis,
    )
    from scripts.emotion_state_phase_b_features import (
        extract_acoustic_features_bytes,
    )

    if (
        not callable(read_verified_audio)
        or not callable(read_verified_ami)
        or read_verified_audio is read_verified_ami
        or type(tracked_evidence) is not dict
        or any(type(name) is not str for name in tracked_evidence)
        or tuple(tracked_evidence) != TRACKED_DATASET_EVIDENCE_FILENAMES
    ):
        raise PublicMaterialPrerequisiteError(
            "exact evidence and two distinct byte-reader capabilities are required"
        )
    if (
        type(authorities) is not dict
        or any(type(role) is not str for role in authorities)
        or tuple(authorities) != NON_LOCKBOX_ROLE_ORDER
    ):
        raise PublicMaterialPrerequisiteError(
            "production authorities must be exactly the three non-lockbox roles"
        )
    authority_snapshot = {
        role: authorities[role] for role in NON_LOCKBOX_ROLE_ORDER
    }
    manifest, records_by_role = _validated_production_role_algebra(
        authorities=authority_snapshot,
        split_manifest=split_manifest,
    )
    (
        validated_configuration,
        validated_environment,
        validated_feature_schema,
        validated_split_schema,
    ) = _validated_non_lockbox_static_mappings(
        configuration=configuration,
        environment_lock=environment_lock,
        feature_schema=feature_schema,
        split_schema=split_schema,
    )
    configuration_sha256 = _canonical_digest(validated_configuration)
    if configuration_sha256 != manifest["configuration_sha256"]:
        raise PublicMaterialPrerequisiteError(
            "configuration identity does not match split authority"
        )
    evidence_snapshot = _tracked_evidence_snapshot(tracked_evidence)
    frozen_tracked_authority = _validated_non_lockbox_tracked_authority(
        tracked_authority
    )
    audio_sources = _selected_nonfinal_audio_sources(
        tracked_authority=frozen_tracked_authority,
        records_by_role=records_by_role,
    )
    ami_sources = _select_ami_source_identities(frozen_tracked_authority)
    tracked_commitment = tracked_public_authority_commitment_sha256(
        tracked_evidence=evidence_snapshot,
        authority=frozen_tracked_authority,
    )
    model_seed = int(configuration_sha256[:8], 16)
    model_identity = frozen_model_identity(model_seed)

    feature_caches: dict[str, dict[str, Any]] = {}
    partition_evidence: dict[str, Any] = {}
    for role in NON_LOCKBOX_ROLE_ORDER:
        feature_rows: list[dict[str, float]] = []
        for source in audio_sources[role]:
            content = read_verified_audio(source)
            if (
                type(content) is not bytes
                or len(content) != source.size_bytes
                or _sha256(content) != source.sha256
            ):
                raise PublicMaterialPrerequisiteError(
                    f"{role} audio bytes do not match sealed identity"
                )
            feature_rows.append(_exact_feature_values(
                extract_acoustic_features_bytes(content)
            ))
        cache = _build_acoustic_feature_cache(
            role=role,
            authority=authority_snapshot[role],
            feature_rows=feature_rows,
            tracked_public_authority_commitment_sha256=tracked_commitment,
            environment_lock_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "environment_lock_sha256"
            ],
            feature_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "feature_schema_sha256"
            ],
            split_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "split_schema_sha256"
            ],
            _validated_records=records_by_role[role],
        )
        feature_caches[role] = cache
        partition_evidence[role] = _partition_evidence_from_feature_cache(
            role=role,
            authority=authority_snapshot[role],
            records=records_by_role[role],
            cache=cache,
            configuration=validated_configuration,
            environment_lock=validated_environment,
            feature_schema=validated_feature_schema,
            split_schema=validated_split_schema,
            model_identity=model_identity,
        )

    diagnostic_probabilities, diagnostic, _thresholds = (
        _evaluate_non_lockbox_partition_evidence(
            partition_evidence=partition_evidence,
            model_seed=model_seed,
            configuration=validated_configuration,
        )
    )

    metadata, words, segments, dialogue_acts, participants = (
        _ami_loader_inputs(
            selected_sources=ami_sources,
            read_verified_ami=read_verified_ami,
        )
    )
    meetings = load_ami_meeting_evidence_v2(
        metadata,
        words,
        segments,
        dialogue_acts,
        frozen_tracked_authority.ami_official_order,
        participant_metadata=participants,
    )
    membership = {
        name: identifiers
        for name, identifiers
        in frozen_tracked_authority.ami_partition_membership
    }
    ami_aggregate = contribution_limited_aggregates_v2(
        meetings,
        membership,
        frozen_tracked_authority.ami_official_order,
        minimum_contributors=MINIMUM_UNIQUE_ACTORS,
    )
    serialized_meetings = [
        _serialize_ami_meeting(meeting) for meeting in meetings
    ]
    try:
        validate_ami_mechanics_aggregates_v2(
            ami_aggregate,
            meetings=serialized_meetings,
            partition_membership=membership,
            official_order=frozen_tracked_authority.ami_official_order,
            minimum_contributors=MINIMUM_UNIQUE_ACTORS,
        )
        validate_published_ami_aggregate_v2(ami_aggregate)
    except (TypeError, ValueError) as error:
        raise PublicMaterialPrerequisiteError(
            f"AMI v2 aggregate is invalid: {error}"
        ) from error
    ami_evidence = _build_ami_evidence_cache(
        tracked_authority=frozen_tracked_authority,
        meetings=meetings,
        aggregate=ami_aggregate,
        tracked_public_authority_commitment_sha256=tracked_commitment,
    )

    slices = _build_frozen_diagnostic_slice_mapping(
        training_authority=authority_snapshot["training_discovery"],
        training_feature_cache=feature_caches["training_discovery"],
        diagnostic_authority=authority_snapshot["balanced_diagnostic"],
        diagnostic_feature_cache=feature_caches["balanced_diagnostic"],
        _validated_training_records=records_by_role["training_discovery"],
        _validated_diagnostic_records=records_by_role[
            "balanced_diagnostic"
        ],
        _feature_caches_are_validated=True,
    )
    diagnostic_slices = mint_slice_analysis(
        diagnostic_probabilities,
        diagnostic,
        slices,
    )
    cache_commitments = _artifact_cache_commitments(
        feature_caches=feature_caches,
        ami_evidence=ami_evidence,
    )
    review_packet = build_non_lockbox_review_packet(
        diagnostic_aggregate=diagnostic.to_payload(),
        diagnostic_slice_analysis=diagnostic_slices.to_payload(),
        ami_aggregate=ami_evidence["aggregate"],
        artifact_cache_commitments=cache_commitments,
        split_manifest_sha256=manifest["split_manifest_sha256"],
        tracked_public_authority_commitment_sha256=tracked_commitment,
    )
    if review_packet["artifact_cache_commitments"] != cache_commitments:
        raise PublicMaterialPrerequisiteError(
            "packet cache commitments do not match minted artifacts"
        )
    return ProductionNonLockboxArtifacts(
        feature_caches=copy.deepcopy(feature_caches),
        ami_evidence=copy.deepcopy(ami_evidence),
        review_packet=copy.deepcopy(review_packet),
    )


def restore_production_non_lockbox_artifacts(
    *,
    authorities: Mapping[str, "ValidatedPartitionAuthority"],
    split_manifest: Mapping[str, Any],
    feature_caches: Mapping[str, Mapping[str, Any]],
    ami_evidence: Mapping[str, Any],
    review_packet: Mapping[str, Any],
    configuration: Mapping[str, Any],
    environment_lock: Mapping[str, Any],
    feature_schema: Mapping[str, Any],
    split_schema: Mapping[str, Any],
) -> ProductionNonLockboxArtifacts:
    from scripts.emotion_state_phase_b_evaluation import (
        frozen_model_identity,
        mint_slice_analysis,
    )

    if (
        type(feature_caches) is not dict
        or any(type(role) is not str for role in feature_caches)
        or tuple(feature_caches) != NON_LOCKBOX_ROLE_ORDER
        or any(type(cache) is not dict for cache in feature_caches.values())
        or type(ami_evidence) is not dict
        or type(review_packet) is not dict
    ):
        raise PublicMaterialPrerequisiteError(
            "persisted non-lockbox artifacts do not match exact shape"
        )
    manifest, records_by_role = _validated_production_role_algebra(
        authorities=authorities,
        split_manifest=split_manifest,
    )
    (
        validated_configuration,
        validated_environment,
        validated_feature_schema,
        validated_split_schema,
    ) = _validated_non_lockbox_static_mappings(
        configuration=configuration,
        environment_lock=environment_lock,
        feature_schema=feature_schema,
        split_schema=split_schema,
    )
    configuration_sha256 = _canonical_digest(validated_configuration)
    if configuration_sha256 != manifest["configuration_sha256"]:
        raise PublicMaterialPrerequisiteError(
            "configuration identity does not match split authority"
        )
    packet = validate_non_lockbox_review_packet(review_packet)
    if packet["split_manifest_sha256"] != manifest["split_manifest_sha256"]:
        raise PublicMaterialPrerequisiteError(
            "packet split identity does not match restored authority"
        )
    tracked_commitment = packet[
        "tracked_public_authority_commitment_sha256"
    ]

    validated_caches: dict[str, dict[str, Any]] = {}
    for role in NON_LOCKBOX_ROLE_ORDER:
        validated_caches[role] = _validate_acoustic_feature_cache(
            feature_caches[role],
            role=role,
            authority=authorities[role],
            tracked_public_authority_commitment_sha256=tracked_commitment,
            environment_lock_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "environment_lock_sha256"
            ],
            feature_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "feature_schema_sha256"
            ],
            split_schema_sha256=EXPECTED_EVIDENCE_IDENTITY_SHA256[
                "split_schema_sha256"
            ],
            _validated_records=records_by_role[role],
        )
    validated_ami = _validate_source_silent_ami_evidence_cache(
        ami_evidence,
        tracked_public_authority_commitment_sha256=tracked_commitment,
    )
    actual_commitments = _artifact_cache_commitments(
        feature_caches=validated_caches,
        ami_evidence=validated_ami,
    )
    if not _matches_packet_contract_exactly(
        packet["artifact_cache_commitments"],
        actual_commitments,
    ):
        raise PublicMaterialPrerequisiteError(
            "packet cache commitments do not match restored artifacts"
        )

    model_seed = int(configuration_sha256[:8], 16)
    model_identity = frozen_model_identity(model_seed)
    partition_evidence = {
        role: _partition_evidence_from_feature_cache(
            role=role,
            authority=authorities[role],
            records=records_by_role[role],
            cache=validated_caches[role],
            configuration=validated_configuration,
            environment_lock=validated_environment,
            feature_schema=validated_feature_schema,
            split_schema=validated_split_schema,
            model_identity=model_identity,
        )
        for role in NON_LOCKBOX_ROLE_ORDER
    }
    diagnostic_probabilities, diagnostic, _thresholds = (
        _evaluate_non_lockbox_partition_evidence(
            partition_evidence=partition_evidence,
            model_seed=model_seed,
            configuration=validated_configuration,
        )
    )
    slices = _build_frozen_diagnostic_slice_mapping(
        training_authority=authorities["training_discovery"],
        training_feature_cache=validated_caches["training_discovery"],
        diagnostic_authority=authorities["balanced_diagnostic"],
        diagnostic_feature_cache=validated_caches["balanced_diagnostic"],
        _validated_training_records=records_by_role["training_discovery"],
        _validated_diagnostic_records=records_by_role[
            "balanced_diagnostic"
        ],
        _feature_caches_are_validated=True,
    )
    diagnostic_slices = mint_slice_analysis(
        diagnostic_probabilities,
        diagnostic,
        slices,
    )
    rebuilt_packet = build_non_lockbox_review_packet(
        diagnostic_aggregate=diagnostic.to_payload(),
        diagnostic_slice_analysis=diagnostic_slices.to_payload(),
        ami_aggregate=validated_ami["aggregate"],
        artifact_cache_commitments=actual_commitments,
        split_manifest_sha256=manifest["split_manifest_sha256"],
        tracked_public_authority_commitment_sha256=tracked_commitment,
    )
    comparisons = (
        *(
            (feature_caches[role], validated_caches[role])
            for role in NON_LOCKBOX_ROLE_ORDER
        ),
        (ami_evidence, validated_ami),
        (review_packet, rebuilt_packet),
    )
    if any(
        _canonical_artifact_bytes(supplied)
        != _canonical_artifact_bytes(rebuilt)
        for supplied, rebuilt in comparisons
    ):
        raise PublicMaterialPrerequisiteError(
            "persisted non-lockbox artifacts do not replay canonically"
        )
    return ProductionNonLockboxArtifacts(
        feature_caches=copy.deepcopy(validated_caches),
        ami_evidence=copy.deepcopy(validated_ami),
        review_packet=copy.deepcopy(rebuilt_packet),
    )
