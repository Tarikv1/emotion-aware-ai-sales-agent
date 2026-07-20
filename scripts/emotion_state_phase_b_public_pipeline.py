from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from scripts.emotion_state_public_dataset_contracts import (
    PublicDatasetContractError,
    classify_ami_member,
    validate_dataset_manifest,
)
from scripts.validate_emotion_state_002_phase_b import (
    EXPECTED_DATASET_EVIDENCE,
    EXPECTED_EVIDENCE_IDENTITY_SHA256,
    EXPECTED_CONFIG,
    EXPECTED_METRIC_DEFINITIONS,
    EXPECTED_SLICE_DEFINITIONS,
    MINIMUM_UNIQUE_ACTORS,
    validate_evaluation_result,
    validate_published_ami_aggregate_v2,
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


def _matches_packet_contract_exactly(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, Mapping):
        return set(actual) == set(expected) and all(
            _matches_packet_contract_exactly(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _matches_packet_contract_exactly(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )
    return actual == expected


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
    validate_aggregate_privacy(diagnostic)
    validate_aggregate_privacy(ami)
    packet: dict[str, Any] = {
        "schema_id": "emotion-state-phase-b-non-lockbox-review-v3",
        "schema_version": 3,
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
        != "emotion-state-phase-b-non-lockbox-review-v3"
        or packet["schema_version"] != 3
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
    if (
        type(packet["split_manifest_sha256"]) is not str
        or _SHA256_PATTERN.fullmatch(packet["split_manifest_sha256"])
        is None
    ):
        raise PublicMaterialPrerequisiteError(
            "split manifest identity is invalid"
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
        not isinstance(lockbox_access, Mapping)
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
