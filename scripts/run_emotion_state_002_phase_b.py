#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import stat
import sys
import uuid
from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Callable, Literal, NoReturn

if TYPE_CHECKING:
    from scripts.emotion_state_phase_b_evaluation import ValidatedPartitionAuthority

if os.name == "nt":
    import msvcrt
else:
    import fcntl


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_emotion_state_002_phase_b import (
    EXPECTED_CONFIG,
    EXPECTED_EVIDENCE_IDENTITY_SHA256,
    EXPECTED_ENVIRONMENT_LOCK,
    EXPECTED_FEATURE_SCHEMA,
    EXPECTED_PUBLIC_RAW_SOURCE_SHA256,
    EXPECTED_SPLIT_SCHEMA,
    EXPECTED_VALIDITY,
    EXPECTED_STATIC_FILE_SHA256,
    derive_phase_b_decision,
    canonical_payload_sha256,
    serialized_decision_evidence_mint_sha256,
    validate_config,
    validate_config_feature_schema_binding,
    validate_decision_inputs,
    validate_environment_identity_bytes,
    validate_environment_lock,
    validate_feature_schema,
    validate_installed_environment_identity,
    validate_lockbox_ami_input,
    validate_lockbox_lineage,
    validate_lockbox_result,
    validate_non_lockbox_packet,
    validate_phase_b_input_ledger,
    validate_phase_b_partition_authority_cache,
    validate_phase_b_result,
    validate_phase_b_split_manifest,
    validate_split_schema,
    validated_lockbox_summary,
)
from scripts.emotion_state_phase_b_public_pipeline import (
    EXPECTED_AMI_SELECTED_SOURCE_COUNT,
    EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT,
    EXPECTED_PRODUCTION_FINAL_LOCKBOX_RECORD_COUNT,
    EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT,
    EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS,
    NON_LOCKBOX_ROLE_ORDER,
    ProductionNonLockboxArtifacts,
    ProductionPreflightArtifacts,
    SourceByteIdentity,
    TRACKED_DATASET_EVIDENCE_FILENAMES,
    TrackedPublicAuthority,
    build_production_non_lockbox_artifacts,
    build_production_preflight_artifacts,
    restore_production_non_lockbox_artifacts,
    tracked_public_authority_commitment_sha256,
    validate_non_lockbox_review_packet,
    validate_tracked_public_evidence,
)


STATE_SCHEMA_VERSION = 1
TRANSACTION_SCHEMA_VERSION = 1
RECEIPT_SCHEMA_VERSION = 1
JOURNAL_NAME = "transaction.json"
LOCK_NAME = "publication.lock"
LOCKBOX_LOCK_NAME = "lockbox.lock"
LOCKBOX_RESERVATION_NAME = "lockbox-reservation.json"
MATERIAL_PIPELINE_LOCK_NAME = "material-pipeline.lock"
OPAQUE_POST_NON_LOCKBOX_STATE_ROOT_ENTRY_NAMES = frozenset({
    LOCKBOX_LOCK_NAME,
    LOCKBOX_RESERVATION_NAME,
    "lockbox",
    "publication",
})
NONFINAL_PARTITION_ROLES = (
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
)
NON_LOCKBOX_FEATURE_CACHE_FIELDS = (
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
NON_LOCKBOX_FEATURE_RECORD_FIELDS = (
    "clip_stem",
    "audio_sha256",
    "audio_size_bytes",
    "features",
)
NON_LOCKBOX_AMI_EVIDENCE_FIELDS = (
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
UNSET_DIGEST = "0" * 64
PRIVATE_COMPONENTS = frozenset(
    {"private", "private-restricted", "secrets", ".secrets"}
)
REPOSITORY_METADATA_COMPONENTS = frozenset({".git", ".hg", ".svn"})
FORBIDDEN_RUNTIME_PREFIXES = (
    "runtime",
    "apps",
    "sales_agent",
)
CREDENTIAL_ENV_NAMES = frozenset(
    {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AZURE_CLIENT_SECRET",
        "ELEVENLABS_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "HUGGINGFACE_TOKEN",
        "OPENAI_API_KEY",
    }
)
CREDENTIAL_ENV_SUFFIXES = (
    "_API_KEY",
    "_ACCESS_TOKEN",
    "_AUTH_TOKEN",
    "_CLIENT_SECRET",
    "_CREDENTIAL",
    "_PASSWORD",
    "_SECRET",
    "_TOKEN",
)
NETWORK_CONFIGURATION_ENV_NAMES = frozenset(
    {
        "CURL_CA_BUNDLE",
        "HF_ENDPOINT",
        "PIP_EXTRA_INDEX_URL",
        "PIP_INDEX_URL",
        "PIP_TRUSTED_HOST",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
    }
)
NETWORK_CONFIGURATION_ENV_SUFFIXES = ("_PROXY",)
_CREMA_AUDIO_SOURCE_PREFIX = (
    "data/public/emotion-state/crema-d-v1.0/repository/AudioWAV/"
)
_AMI_SOURCE_ROOT = (
    "data/public/emotion-state/ami-manual-annotations-v1.6.2/"
)
_AMI_EXTRACTED_SOURCE_ROOT = f"{_AMI_SOURCE_ROOT}extracted/"
_AMI_MEETING_UNIVERSE_SOURCE = (
    f"{_AMI_EXTRACTED_SOURCE_ROOT}corpusResources/meetings.xml"
)
_AMI_PARTICIPANTS_SOURCE = (
    f"{_AMI_EXTRACTED_SOURCE_ROOT}corpusResources/participants.xml"
)
_AMI_EXCLUDED_SOURCES = frozenset(
    {
        f"{_AMI_SOURCE_ROOT}ami_manual_1.6.2.zip",
        f"{_AMI_SOURCE_ROOT}official-partitions/datasets.shtml",
        f"{_AMI_EXTRACTED_SOURCE_ROOT}AMI-metadata.xml",
    }
)
ALLOWED_PHASES = frozenset(
    {
        "initialized",
        "preflight_complete",
        "non_lockbox_complete",
        "lockbox_complete",
        "awaiting_acceptance",
        "accepted",
        "rejected",
    }
)
ALLOWED_TRANSITIONS = {
    "initialized": "preflight_complete",
    "preflight_complete": "non_lockbox_complete",
    "non_lockbox_complete": "lockbox_complete",
    "lockbox_complete": "awaiting_acceptance",
    "awaiting_acceptance": frozenset({"accepted", "rejected"}),
}
STATE_FIELDS = frozenset(
    {
        "schema_version",
        "phase",
        "configuration_sha256",
        "environment_lock_sha256",
        "input_ledger_sha256",
        "split_manifest_sha256",
        "non_lockbox_packet_sha256",
        "lockbox_open_count",
        "lockbox_result_sha256",
        "lockbox_decision_evidence_sha256",
        "lockbox_decision_evidence_mint_sha256",
        "candidate_transaction_id",
    }
)
DIGEST_FIELDS = (
    "configuration_sha256",
    "environment_lock_sha256",
    "input_ledger_sha256",
    "split_manifest_sha256",
    "non_lockbox_packet_sha256",
    "lockbox_result_sha256",
    "lockbox_decision_evidence_sha256",
    "lockbox_decision_evidence_mint_sha256",
)
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_TRANSACTION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_RECEIPT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")
_UNJOURNALED_NAME_PATTERN = re.compile(
    r"^[0-9a-f]{32}\.(?:result|report)\.(?:stage|backup|restore)$"
    r"|^[0-9a-f]{32}\.journal\.stage$"
)
_REPLACE_INTENT_SCHEMA_VERSION = 1
_PATH_IDENTITY_PROOFS: dict[str, tuple[tuple[str, int, int], ...]] = {}


class RunnerError(RuntimeError):
    """A fail-closed Phase B runner or publication error."""


@dataclass(frozen=True)
class VerifiedMaterialBytes:
    logical_name: str
    content: bytes
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class _DirectoryAuthority:
    path: Path
    posix_descriptor: int | None = None
    windows_handle: int | None = None


@dataclass(frozen=True, slots=True)
class _HeldDirectoryAuthority:
    path: Path
    stable_identity: tuple[int, ...]
    posix_descriptor: int | None
    windows_handle: int | None


@dataclass(frozen=True, slots=True)
class _MaterialPipelineAuthority:
    state_root: _HeldDirectoryAuthority
    lock_path: Path
    lock_stable_identity: tuple[int, ...]
    lock_file: BinaryIO


@dataclass(frozen=True, slots=True)
class _PreflightOutputAuthorities:
    inputs_root: _HeldDirectoryAuthority
    split_root: _HeldDirectoryAuthority
    preflight_root: _HeldDirectoryAuthority


@dataclass(frozen=True, slots=True)
class _NonLockboxOutputAuthorities:
    root: _HeldDirectoryAuthority
    cache_root: _HeldDirectoryAuthority


@dataclass(slots=True)
class _PreflightArtifactRecoveryPlan:
    destination: Path
    parent_authority: _HeldDirectoryAuthority
    action: Literal[
        "none",
        "discard-stage",
        "finish-committed",
        "restore-prior",
        "discard-uncommitted-stage",
    ]
    destination_file: _HeldRegularFileAuthority | None
    intent_file: _HeldRegularFileAuthority | None
    prior_file: _HeldRegularFileAuthority | None
    stage_file: _HeldRegularFileAuthority | None


@dataclass(slots=True)
class _NonLockboxArtifactRecoveryPlan:
    destination: Path
    parent_authority: _HeldDirectoryAuthority
    action: Literal[
        "none",
        "discard-stage",
        "finish-committed",
        "restore-prior",
        "discard-uncommitted-stage",
    ]
    destination_file: _HeldRegularFileAuthority | None
    intent_file: _HeldRegularFileAuthority | None
    prior_file: _HeldRegularFileAuthority | None
    stage_file: _HeldRegularFileAuthority | None


@dataclass(frozen=True, slots=True)
class _HeldRegularFileAuthority:
    path: Path
    stable_identity: tuple[int, ...]
    sha256: str
    size_bytes: int
    posix_descriptor: int | None
    windows_handle: int | None


@dataclass(slots=True)
class _RegularFileAuthorityOwner:
    authority: _HeldRegularFileAuthority | None

    def peek(self) -> _HeldRegularFileAuthority | None:
        return self.authority

    def take(self) -> _HeldRegularFileAuthority:
        authority = self.authority
        if authority is None:
            raise RunnerError("regular-file authority owner is already consumed")
        self.authority = None
        return authority

    def restore(self, authority: _HeldRegularFileAuthority) -> None:
        if self.authority is not None:
            raise RunnerError("regular-file authority owner is not empty")
        self.authority = authority


@dataclass(frozen=True, slots=True)
class _AdmittedStateAuthority:
    admission: Literal["absent", "initialized"]
    state_root_stable_identity: tuple[int, ...]
    initial_bytes: bytes | None
    initial_file: _HeldRegularFileAuthority | None
    _initial_owner: _RegularFileAuthorityOwner | None


@dataclass(frozen=True, slots=True)
class _AdmittedNonLockboxStateAuthority:
    initial_state: dict[str, Any]
    initial_bytes: bytes
    initial_file: _HeldRegularFileAuthority
    _initial_owner: _RegularFileAuthorityOwner


@dataclass(frozen=True, slots=True)
class _HeldCommittedStateAuthority:
    state: dict[str, Any]
    canonical_bytes: bytes
    file: _HeldRegularFileAuthority
    _file_owner: _RegularFileAuthorityOwner


@dataclass(frozen=True, slots=True)
class _PersistedPreflightReadback:
    input_ledger: dict[str, Any]
    split_manifest: dict[str, Any]
    files: tuple[_HeldRegularFileAuthority, ...]


@dataclass(frozen=True, slots=True)
class _PersistedNonLockboxReadback:
    feature_caches: tuple[dict[str, Any], ...]
    ami_evidence: dict[str, Any]
    review_packet: dict[str, Any]
    files: tuple[_HeldRegularFileAuthority, ...]


@dataclass(frozen=True, slots=True)
class _HeldStaticPreflightInputs:
    configuration: dict[str, Any]
    contents: tuple[bytes, ...]
    digests: tuple[str, ...]
    files: tuple[_HeldRegularFileAuthority, ...]


@dataclass(frozen=True, slots=True)
class _HeldEnvironmentWheelInputs:
    filenames: tuple[str, ...]
    contents: tuple[bytes, ...]
    digests: tuple[str, ...]
    files: tuple[_HeldRegularFileAuthority, ...]


@dataclass(frozen=True, slots=True)
class _HeldTrackedPublicEvidenceInputs:
    names: tuple[str, ...]
    contents: tuple[bytes, ...]
    digests: tuple[str, ...]
    files: tuple[_HeldRegularFileAuthority, ...]


@dataclass(frozen=True, slots=True)
class _CommittedPreflightReadback:
    state: dict[str, Any]
    state_file: _HeldRegularFileAuthority
    artifacts: _PersistedPreflightReadback
    restored: tuple[ValidatedPartitionAuthority, ...]


@dataclass(frozen=True)
class RunnerPaths:
    project_root: Path
    input_root: Path
    state_root: Path
    canonical_root: Path
    config_path: Path
    environment_lock_path: Path
    feature_schema_path: Path
    split_schema_path: Path
    split_manifest_path: Path
    input_ledger_path: Path
    non_lockbox_packet_path: Path
    lockbox_result_path: Path | None
    public_material_root: Path | None = None
    authority: str = "invalid"

    @classmethod
    def production(cls) -> "RunnerPaths":
        root = ROOT
        state_root = root / ".tmp" / "emotion-state-002-phase-b-cut4b"
        canonical_root = (
            root
            / "research"
            / "experiments"
            / "generated"
            / "EMOTION-STATE-002-phase-b-public-data-feasibility"
        )
        return cls(
            project_root=root,
            input_root=root,
            state_root=state_root,
            canonical_root=canonical_root,
            config_path=(
                root
                / "research"
                / "experiments"
                / "cases"
                / "emotion-state-002-phase-b-config.json"
            ),
            environment_lock_path=(
                root
                / "research"
                / "environments"
                / "emotion-state-002"
                / "requirements.lock"
            ),
            feature_schema_path=(
                root
                / "research"
                / "sources"
                / "emotion_state"
                / "emotion_state_phase_b_feature_v2.schema.json"
            ),
            split_schema_path=(
                root
                / "research"
                / "sources"
                / "emotion_state"
                / "emotion_state_evaluation_split_v1.schema.json"
            ),
            split_manifest_path=(
                state_root / "split" / "validated-split-manifest.json"
            ),
            input_ledger_path=state_root / "inputs" / "input-ledger.json",
            non_lockbox_packet_path=(
                state_root / "non-lockbox" / "non-lockbox-packet.json"
            ),
            lockbox_result_path=None,
            public_material_root=root / "data" / "public" / "emotion-state",
            authority="production",
        )

    @classmethod
    def for_testing(
        cls,
        *,
        project_root: Path,
        input_root: Path,
        state_root: Path,
        canonical_root: Path,
        config_path: Path,
        environment_lock_path: Path,
        feature_schema_path: Path,
        split_schema_path: Path,
        split_manifest_path: Path,
        input_ledger_path: Path,
        non_lockbox_packet_path: Path,
        lockbox_result_path: Path,
        public_material_root: Path | None = None,
    ) -> "RunnerPaths":
        return cls(
            project_root=project_root,
            input_root=input_root,
            state_root=state_root,
            canonical_root=canonical_root,
            config_path=config_path,
            environment_lock_path=environment_lock_path,
            feature_schema_path=feature_schema_path,
            split_schema_path=split_schema_path,
            split_manifest_path=split_manifest_path,
            input_ledger_path=input_ledger_path,
            non_lockbox_packet_path=non_lockbox_packet_path,
            lockbox_result_path=lockbox_result_path,
            public_material_root=public_material_root,
            authority="injected-test",
        )

    @property
    def state_path(self) -> Path:
        return Path(self.state_root) / "state.json"

    @property
    def material_pipeline_lock_path(self) -> Path:
        return Path(self.state_root) / MATERIAL_PIPELINE_LOCK_NAME

    @property
    def preflight_state_stage_path(self) -> Path:
        return Path(self.state_root) / ".state.json.preflight.stage"

    @property
    def non_lockbox_state_stage_path(self) -> Path:
        return Path(self.state_root) / ".state.json.non-lockbox.stage"

    @property
    def non_lockbox_state_intent_path(self) -> Path:
        return Path(self.state_root) / ".state.json.non-lockbox.intent.json"

    @property
    def non_lockbox_state_prior_path(self) -> Path:
        return Path(self.state_root) / ".state.json.non-lockbox.prior"

    def partition_authority_cache_path(self, role: str) -> Path:
        if type(role) is not str or role not in NONFINAL_PARTITION_ROLES:
            raise RunnerError("preflight partition role is invalid")
        return self.preflight_cache_root / f"{role}.json"

    def non_lockbox_feature_cache_path(self, role: str) -> Path:
        if type(role) is not str or role not in NONFINAL_PARTITION_ROLES:
            raise RunnerError("non-lockbox feature-cache role is invalid")
        return self.non_lockbox_cache_root / f"{role}.json"

    @property
    def non_lockbox_ami_evidence_path(self) -> Path:
        return self.non_lockbox_cache_root / "ami-v2-evidence.json"

    @property
    def non_lockbox_root(self) -> Path:
        return Path(self.state_root) / "non-lockbox"

    @property
    def preflight_cache_root(self) -> Path:
        return Path(self.state_root) / "preflight"

    @property
    def non_lockbox_cache_root(self) -> Path:
        return self.non_lockbox_root / "cache"

    @property
    def lockbox_root(self) -> Path:
        return Path(self.state_root) / "lockbox"

    @property
    def final_lockbox_cache_root(self) -> Path:
        return self.lockbox_root / "cache"

    @property
    def crema_material_root(self) -> Path:
        if self.public_material_root is None:
            raise RunnerError("public-material root is unavailable")
        return Path(self.public_material_root) / "crema-d-v1.0"

    @property
    def crema_audio_root(self) -> Path:
        return self.crema_material_root / "repository" / "AudioWAV"

    @property
    def crema_finished_responses_path(self) -> Path:
        return self.crema_material_root / "repository" / "finishedResponses.csv"

    @property
    def crema_summary_table_path(self) -> Path:
        return (
            self.crema_material_root
            / "repository"
            / "processedResults"
            / "summaryTable.csv"
        )

    @property
    def ami_material_root(self) -> Path:
        if self.public_material_root is None:
            raise RunnerError("public-material root is unavailable")
        return Path(self.public_material_root) / "ami-manual-annotations-v1.6.2"

    @property
    def ami_archive_path(self) -> Path:
        return self.ami_material_root / "ami_manual_1.6.2.zip"

    @property
    def ami_extracted_root(self) -> Path:
        return self.ami_material_root / "extracted"

    @property
    def ami_partition_source_path(self) -> Path:
        return (
            self.ami_material_root
            / "official-partitions"
            / "datasets.shtml"
        )

    @property
    def dataset_evidence_root(self) -> Path:
        return (
            Path(self.project_root)
            / "research"
            / "sources"
            / "emotion_state"
            / "datasets"
        )

    @property
    def recovery_root(self) -> Path:
        return Path(self.state_root) / "publication"

    @property
    def journal_path(self) -> Path:
        return self.recovery_root / JOURNAL_NAME

    @property
    def lockbox_lock_path(self) -> Path:
        return Path(self.state_root) / LOCKBOX_LOCK_NAME

    @property
    def lockbox_reservation_path(self) -> Path:
        return Path(self.state_root) / LOCKBOX_RESERVATION_NAME

    @property
    def result_path(self) -> Path:
        return Path(self.canonical_root) / "result.json"

    @property
    def report_path(self) -> Path:
        return Path(self.canonical_root) / "report.md"

    def receipt_path(self, receipt_name: str) -> Path:
        return self.recovery_root / _validate_receipt_name(receipt_name)


def canonical_json_bytes(payload: Any) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RunnerError("payload is not canonical JSON") from error


def _non_lockbox_artifact_json_bytes(payload: Any) -> bytes:
    """Render frozen insertion-order artifacts as deterministic LF JSON."""
    try:
        return (
            json.dumps(
                payload,
                indent=2,
                sort_keys=False,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RunnerError("non-lockbox artifact is not deterministic JSON") from error


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


def _mapping_digest(payload: Mapping[str, Any]) -> str:
    content = (
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return _sha256_bytes(content)


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(_read_file_nofollow(path))


def _sha256_descriptor(descriptor: int) -> str:
    position = os.lseek(descriptor, 0, os.SEEK_CUR)
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1_048_576)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest().upper()
    finally:
        os.lseek(descriptor, position, os.SEEK_SET)


def _windows_handle_information(handle: int) -> tuple[tuple[int, ...], int, int, int]:
    from ctypes import wintypes

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = (
            ("FileAttributes", wintypes.DWORD),
            ("CreationTimeLow", wintypes.DWORD),
            ("CreationTimeHigh", wintypes.DWORD),
            ("LastAccessTimeLow", wintypes.DWORD),
            ("LastAccessTimeHigh", wintypes.DWORD),
            ("LastWriteTimeLow", wintypes.DWORD),
            ("LastWriteTimeHigh", wintypes.DWORD),
            ("VolumeSerialNumber", wintypes.DWORD),
            ("FileSizeHigh", wintypes.DWORD),
            ("FileSizeLow", wintypes.DWORD),
            ("NumberOfLinks", wintypes.DWORD),
            ("FileIndexHigh", wintypes.DWORD),
            ("FileIndexLow", wintypes.DWORD),
        )

    information = ByHandleFileInformation()
    function = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetFileInformationByHandle
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ByHandleFileInformation),
    )
    function.restype = wintypes.BOOL
    if not function(handle, ctypes.byref(information)):
        raise OSError(
            ctypes.get_last_error(),
            "unable to query held Windows handle",
        )
    identity = (
        int(information.VolumeSerialNumber),
        int(information.FileIndexHigh),
        int(information.FileIndexLow),
    )
    size = (int(information.FileSizeHigh) << 32) | int(information.FileSizeLow)
    return (
        identity,
        size,
        int(information.NumberOfLinks),
        int(information.FileAttributes),
    )


def _status_stable_identity(status: os.stat_result | Any) -> tuple[int, ...]:
    if os.name == "nt":
        inode = int(status.st_ino)
        return (
            int(status.st_dev),
            (inode >> 32) & 0xFFFFFFFF,
            inode & 0xFFFFFFFF,
        )
    return (int(status.st_dev), int(status.st_ino))


def _windows_open_raw_handle(
    path: Path,
    *,
    access: int,
    share_mode: int,
    disposition: int,
    directory: bool = False,
) -> int:
    from ctypes import wintypes

    function = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
    function.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    function.restype = wintypes.HANDLE
    flags = 0x00200000  # FILE_FLAG_OPEN_REPARSE_POINT
    flags |= 0x02000000 if directory else 0x00000080
    handle = function(
        str(path),
        access,
        share_mode,
        None,
        disposition,
        flags,
        None,
    )
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        raise OSError(ctypes.get_last_error(), "unable to open held Windows handle")
    return int(handle)


def _windows_close_raw_handle(handle: int) -> None:
    from ctypes import wintypes

    function = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
    function.argtypes = (wintypes.HANDLE,)
    function.restype = wintypes.BOOL
    if not function(handle):
        raise OSError(ctypes.get_last_error(), "unable to close held Windows handle")


def _windows_seek_start(handle: int) -> None:
    from ctypes import wintypes

    function = ctypes.WinDLL("kernel32", use_last_error=True).SetFilePointerEx
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.c_longlong,
        ctypes.POINTER(ctypes.c_longlong),
        wintypes.DWORD,
    )
    function.restype = wintypes.BOOL
    if not function(handle, 0, None, 0):
        raise OSError(ctypes.get_last_error(), "unable to seek held Windows handle")


def _windows_read_raw_handle(handle: int, maximum_bytes: int) -> bytes:
    from ctypes import wintypes

    _windows_seek_start(handle)
    read_file = ctypes.WinDLL("kernel32", use_last_error=True).ReadFile
    read_file.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    read_file.restype = wintypes.BOOL
    chunks: list[bytes] = []
    remaining = maximum_bytes + 1
    while remaining:
        requested = min(1_048_576, remaining)
        buffer = ctypes.create_string_buffer(requested)
        count = wintypes.DWORD()
        if not read_file(
            handle,
            buffer,
            requested,
            ctypes.byref(count),
            None,
        ):
            raise OSError(ctypes.get_last_error(), "unable to read held Windows handle")
        if count.value == 0:
            break
        chunks.append(buffer.raw[:count.value])
        remaining -= count.value
    content = b"".join(chunks)
    if len(content) > maximum_bytes:
        raise RunnerError("held file exceeds the allowed size")
    return content


def _windows_write_raw_handle(handle: int, content: bytes) -> None:
    from ctypes import wintypes

    _windows_seek_start(handle)
    write_file = ctypes.WinDLL("kernel32", use_last_error=True).WriteFile
    write_file.argtypes = (
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    write_file.restype = wintypes.BOOL
    offset = 0
    while offset < len(content):
        chunk = content[offset:offset + 1_048_576]
        buffer = ctypes.create_string_buffer(chunk)
        count = wintypes.DWORD()
        if not write_file(
            handle,
            buffer,
            len(chunk),
            ctypes.byref(count),
            None,
        ) or count.value != len(chunk):
            raise OSError(ctypes.get_last_error(), "unable to write held Windows handle")
        offset += count.value


def _windows_flush_raw_handle(handle: int) -> None:
    from ctypes import wintypes

    function = ctypes.WinDLL("kernel32", use_last_error=True).FlushFileBuffers
    function.argtypes = (wintypes.HANDLE,)
    function.restype = wintypes.BOOL
    if not function(handle):
        raise OSError(ctypes.get_last_error(), "unable to flush held Windows handle")


def _windows_rename_raw_handle(
    handle: int,
    destination_name: str,
    *,
    destination_parent_handle: int,
) -> None:
    from ctypes import wintypes

    encoded_name = destination_name.encode("utf-16-le")

    class FileRenameInfoEx(ctypes.Structure):
        _fields_ = (
            ("Flags", wintypes.DWORD),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        )

    name_offset = FileRenameInfoEx.FileName.offset
    information_size = name_offset + len(encoded_name)
    buffer = ctypes.create_string_buffer(information_size)
    information = FileRenameInfoEx.from_buffer(buffer)
    information.Flags = 0
    information.RootDirectory = destination_parent_handle
    information.FileNameLength = len(encoded_name)
    ctypes.memmove(
        ctypes.addressof(buffer) + name_offset,
        encoded_name,
        len(encoded_name),
    )

    class IoStatusBlock(ctypes.Structure):
        _fields_ = (
            ("Status", ctypes.c_void_p),
            ("Information", ctypes.c_size_t),
        )

    io_status = IoStatusBlock()
    function = ctypes.WinDLL("ntdll", use_last_error=True).NtSetInformationFile
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(IoStatusBlock),
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.c_int,
    )
    function.restype = ctypes.c_long
    status_code = function(
        handle,
        ctypes.byref(io_status),
        buffer,
        information_size,
        65,
    )
    if status_code != 0:
        raise OSError(
            status_code & 0xFFFFFFFF,
            "unable to perform held-handle rename",
        )


def _windows_unlink_raw_handle(handle: int) -> None:
    from ctypes import wintypes

    class FileDispositionInfoEx(ctypes.Structure):
        _fields_ = (("Flags", wintypes.DWORD),)

    information = FileDispositionInfoEx(
        0x00000001 | 0x00000002  # DELETE | POSIX_SEMANTICS
    )
    function = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).SetFileInformationByHandle
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    function.restype = wintypes.BOOL
    if not function(
        handle,
        21,  # FileDispositionInfoEx
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        raise OSError(
            ctypes.get_last_error(),
            "unable to unlink held Windows handle with POSIX semantics",
        )


def _read_file_nofollow(
    path: Path,
    *,
    maximum_bytes: int = 16_777_216,
    require_single_link: bool = False,
) -> bytes:
    """Read a regular file through a no-follow handle and bind its identity."""
    if type(require_single_link) is not bool:
        raise RunnerError("single-link read policy must be a boolean")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        with _trusted_parent_handles(path) as parent_authority:
            parent_descriptor = parent_authority.posix_descriptor
            _verify_cached_path_proof(path)
            if parent_descriptor is None:
                before = os.stat(path, follow_symlinks=False)
                descriptor = os.open(path, flags)
                after = os.stat(path, follow_symlinks=False)
            else:
                before = os.stat(
                    path.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
                after = os.stat(
                    path.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            if _is_link_or_reparse(path, before) or not stat.S_ISREG(
                before.st_mode
            ) or (require_single_link and before.st_nlink != 1):
                os.close(descriptor)
                raise RunnerError(
                    "bound input is not a regular no-follow single-link file"
                    if require_single_link
                    else "bound input is not a regular no-follow file"
                )
            try:
                _verify_cached_path_proof(path)
            except Exception:
                os.close(descriptor)
                raise
    except OSError as error:
        raise RunnerError(f"unable to open bound file: {Path(path).name}") from error
    try:
        opened = os.fstat(descriptor)
        if (
            _is_link_or_reparse(path, after)
            or not stat.S_ISREG(opened.st_mode)
            or (require_single_link and opened.st_nlink != 1)
            or (require_single_link and after.st_nlink != 1)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
            or (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino)
        ):
            raise RunnerError("bound file identity changed during open")
        size = opened.st_size
        if size < 0 or size > maximum_bytes:
            raise RunnerError("bound file exceeds the allowed size")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > maximum_bytes:
            raise RunnerError("bound file exceeds the allowed size")
        final = os.fstat(descriptor)
        if (
            (final.st_dev, final.st_ino, final.st_size)
            != (opened.st_dev, opened.st_ino, opened.st_size)
            or (require_single_link and final.st_nlink != 1)
        ):
            raise RunnerError("bound file changed while being read")
        return content
    except OSError as error:
        raise RunnerError(f"unable to read bound file: {Path(path).name}") from error
    finally:
        os.close(descriptor)


@contextmanager
def _held_directory_authority(path: Path) -> Iterator[_HeldDirectoryAuthority]:
    target = Path(path)
    try:
        status = os.stat(target, follow_symlinks=False)
    except OSError as error:
        raise RunnerError("held directory is unavailable") from error
    if _is_link_or_reparse(target, status) or not stat.S_ISDIR(status.st_mode):
        raise RunnerError("held directory is a symlink, reparse point, or non-directory")
    if os.name == "nt":
        handle = _windows_open_raw_handle(
            target,
            access=0x80000000 | 0x40000000,
            share_mode=0x00000001 | 0x00000002,
            disposition=3,
            directory=True,
        )
        try:
            identity, _size, _links, attributes = _windows_handle_information(handle)
            after = os.stat(target, follow_symlinks=False)
            if (
                identity != _status_stable_identity(status)
                or identity != _status_stable_identity(after)
                or not (attributes & 0x10)
                or attributes & 0x400
                or _is_link_or_reparse(target, after)
            ):
                raise RunnerError("held Windows directory authority is unsafe")
            authority = _HeldDirectoryAuthority(
                path=target,
                stable_identity=identity,
                posix_descriptor=None,
                windows_handle=handle,
            )
            _verify_held_directory_authority(authority)
            yield authority
            _verify_held_directory_authority(authority)
        finally:
            _windows_close_raw_handle(handle)
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError as error:
        raise RunnerError("unable to open held directory authority") from error
    try:
        opened = os.fstat(descriptor)
        after = os.stat(target, follow_symlinks=False)
        if (
            _status_stable_identity(status)
            != _status_stable_identity(opened)
            or _status_stable_identity(after)
            != _status_stable_identity(opened)
            or _is_link_or_reparse(target, after)
        ):
            raise RunnerError("held POSIX directory identity changed during open")
        authority = _HeldDirectoryAuthority(
            path=target,
            stable_identity=(int(opened.st_dev), int(opened.st_ino)),
            posix_descriptor=descriptor,
            windows_handle=None,
        )
        _verify_held_directory_authority(authority)
        yield authority
        _verify_held_directory_authority(authority)
    finally:
        os.close(descriptor)


def _verify_held_directory_authority(authority: _HeldDirectoryAuthority) -> None:
    if type(authority) is not _HeldDirectoryAuthority:
        raise RunnerError("held directory authority type changed")
    if os.name == "nt":
        if authority.windows_handle is None or authority.posix_descriptor is not None:
            raise RunnerError("held Windows directory handle is unavailable")
        identity, _size, _links, attributes = _windows_handle_information(
            authority.windows_handle
        )
        if identity != authority.stable_identity or not (attributes & 0x10) or attributes & 0x400:
            raise RunnerError("held directory identity changed")
    else:
        if authority.posix_descriptor is None or authority.windows_handle is not None:
            raise RunnerError("held POSIX directory descriptor is unavailable")
        opened = os.fstat(authority.posix_descriptor)
        if (int(opened.st_dev), int(opened.st_ino)) != authority.stable_identity:
            raise RunnerError("held directory identity changed")
    inspected = os.stat(authority.path, follow_symlinks=False)
    if _is_link_or_reparse(authority.path, inspected) or not stat.S_ISDIR(
        inspected.st_mode
    ) or _status_stable_identity(inspected) != authority.stable_identity:
        raise RunnerError("held directory path changed")


def _windows_open_child_directory_handle(
    parent_handle: int,
    name: str,
    *,
    create: bool,
) -> int:
    from ctypes import wintypes

    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise RunnerError("child directory name is invalid")

    class UnicodeString(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        )

    class ObjectAttributes(ctypes.Structure):
        _fields_ = (
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        )

    class IoStatusBlock(ctypes.Structure):
        _fields_ = (("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t))

    name_buffer = ctypes.create_unicode_buffer(name)
    encoded_length = len(name.encode("utf-16-le"))
    unicode_name = UnicodeString(
        encoded_length,
        encoded_length + 2,
        ctypes.cast(name_buffer, wintypes.LPWSTR),
    )
    attributes = ObjectAttributes(
        ctypes.sizeof(ObjectAttributes),
        parent_handle,
        ctypes.pointer(unicode_name),
        0x00000040,  # OBJ_CASE_INSENSITIVE
        None,
        None,
    )
    io_status = IoStatusBlock()
    result_handle = wintypes.HANDLE()
    function = ctypes.WinDLL("ntdll", use_last_error=True).NtCreateFile
    function.argtypes = (
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    )
    function.restype = ctypes.c_long
    status_code = int(function(
        ctypes.byref(result_handle),
        0x80000000 | 0x40000000 | 0x00100000,
        ctypes.byref(attributes),
        ctypes.byref(io_status),
        None,
        0x00000080,
        0x00000001 | 0x00000002,
        2 if create else 1,  # FILE_CREATE / FILE_OPEN
        0x00000001 | 0x00000020 | 0x00200000,
        None,
        0,
    ))
    if status_code < 0:
        raise OSError(
            status_code & 0xFFFFFFFF,
            "unable to bind child directory under held parent",
        )
    return int(result_handle.value)


@contextmanager
def _held_child_directory_authority(
    path: Path,
    parent_authority: _HeldDirectoryAuthority,
    *,
    create: bool = True,
) -> Iterator[_HeldDirectoryAuthority]:
    target = Path(path)
    _verify_held_directory_authority(parent_authority)
    if type(create) is not bool:
        raise RunnerError("directory creation policy type changed")
    if target.parent != parent_authority.path:
        raise RunnerError("directory creation parent authority does not match")
    exists = os.path.lexists(target)
    before = os.stat(target, follow_symlinks=False) if exists else None
    if before is not None and (
        _is_link_or_reparse(target, before) or not stat.S_ISDIR(before.st_mode)
    ):
        raise RunnerError("preflight directory entry is unsafe")
    if os.name != "nt":
        if not exists:
            raise RunnerError(
                "POSIX preflight directory creation is not qualified"
            )
        if parent_authority.posix_descriptor is None:
            raise RunnerError("held POSIX parent descriptor is unavailable")
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(
            target.name,
            flags,
            dir_fd=parent_authority.posix_descriptor,
        )
        try:
            opened = os.fstat(descriptor)
            after = os.stat(
                target.name,
                dir_fd=parent_authority.posix_descriptor,
                follow_symlinks=False,
            )
            if (
                before is None
                or _status_stable_identity(before)
                != _status_stable_identity(opened)
                or _status_stable_identity(after)
                != _status_stable_identity(opened)
            ):
                raise RunnerError("held POSIX child directory identity changed")
            authority = _HeldDirectoryAuthority(
                path=target,
                stable_identity=_status_stable_identity(opened),
                posix_descriptor=descriptor,
                windows_handle=None,
            )
            _verify_held_directory_authority(authority)
            yield authority
            _verify_held_directory_authority(authority)
        finally:
            os.close(descriptor)
        return

    if parent_authority.windows_handle is None:
        raise RunnerError("held Windows parent handle is unavailable")
    try:
        handle = _windows_open_child_directory_handle(
            parent_authority.windows_handle,
            target.name,
            create=create and not exists,
        )
    except OSError as error:
        label = "create" if create and not exists else "open"
        raise RunnerError(f"unable to {label} held child directory") from error
    try:
        identity, _size, _links, attributes = _windows_handle_information(handle)
        after = os.stat(target, follow_symlinks=False)
        if (
            not (attributes & 0x10)
            or attributes & 0x400
            or _is_link_or_reparse(target, after)
            or identity != _status_stable_identity(after)
            or (
                before is not None
                and identity != _status_stable_identity(before)
            )
        ):
            raise RunnerError("held Windows child directory identity changed")
        authority = _HeldDirectoryAuthority(
            path=target,
            stable_identity=identity,
            posix_descriptor=None,
            windows_handle=handle,
        )
        _verify_held_directory_authority(authority)
        if not exists and create:
            _flush_held_directory(authority)
            _flush_held_directory(parent_authority)
        yield authority
        _verify_held_directory_authority(authority)
    finally:
        _windows_close_raw_handle(handle)


@contextmanager
def _held_regular_file_with_bytes(
    path: Path,
    *,
    maximum_bytes: int = 268_435_456,
    delete_access: bool = False,
    proof_bound: bool = False,
) -> Iterator[tuple[_HeldRegularFileAuthority, bytes]]:
    target = Path(path)
    if type(delete_access) is not bool:
        raise RunnerError("held-file delete policy type changed")
    if type(proof_bound) is not bool:
        raise RunnerError("held-file proof-bound policy type changed")
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise RunnerError("held-file maximum size is invalid")
    if not proof_bound:
        before = os.stat(target, follow_symlinks=False)
        if (
            _is_link_or_reparse(target, before)
            or not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
        ):
            raise RunnerError(
                "held file must be regular, no-follow, and single-link"
            )
        if os.name == "nt":
            access = 0x80000000 | 0x00000080
            if delete_access:
                access |= 0x00010000
            handle = _windows_open_raw_handle(
                target,
                access=access,
                share_mode=0x00000001,
                disposition=3,
            )
            try:
                identity, size, links, attributes = (
                    _windows_handle_information(handle)
                )
                after = os.stat(target, follow_symlinks=False)
                if (
                    identity != _status_stable_identity(before)
                    or identity != _status_stable_identity(after)
                    or links != 1
                    or attributes & (0x10 | 0x400)
                    or _is_link_or_reparse(target, after)
                ):
                    raise RunnerError("held Windows file authority is unsafe")
                content = _windows_read_raw_handle(handle, maximum_bytes)
                if len(content) != size:
                    raise RunnerError(
                        "held Windows file size changed during read"
                    )
                authority = _HeldRegularFileAuthority(
                    path=target,
                    stable_identity=identity,
                    sha256=_sha256_bytes(content),
                    size_bytes=len(content),
                    posix_descriptor=None,
                    windows_handle=handle,
                )
                yield authority, content
            finally:
                _windows_close_raw_handle(handle)
            return
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        if delete_access:
            flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target, flags)
        try:
            opened = os.fstat(descriptor)
            after = os.stat(target, follow_symlinks=False)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise RunnerError("held POSIX file authority is unsafe")
            if (
                _status_stable_identity(before)
                != _status_stable_identity(opened)
                or _status_stable_identity(after)
                != _status_stable_identity(opened)
                or _is_link_or_reparse(target, after)
            ):
                raise RunnerError("held POSIX file identity changed during open")
            content = _read_posix_descriptor_bytes(descriptor, maximum_bytes)
            authority = _HeldRegularFileAuthority(
                path=target,
                stable_identity=(int(opened.st_dev), int(opened.st_ino)),
                sha256=_sha256_bytes(content),
                size_bytes=len(content),
                posix_descriptor=descriptor,
                windows_handle=None,
            )
            yield authority, content
        finally:
            os.close(descriptor)
        return
    with _trusted_parent_handles(
        target,
        include_target=False,
        mutation=delete_access,
    ) as parent_authority:
        _verify_cached_path_proof(target)
        if os.name == "nt":
            before = os.stat(target, follow_symlinks=False)
            if (
                _is_link_or_reparse(target, before)
                or not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
            ):
                raise RunnerError(
                    "held file must be regular, no-follow, and single-link"
                )
            access = 0x80000000 | 0x00000080
            if delete_access:
                access |= 0x00010000
            handle = _windows_open_raw_handle(
                target,
                access=access,
                share_mode=0x00000001,
                disposition=3,
            )
            try:
                _verify_cached_path_proof(target)
                identity, size, links, attributes = (
                    _windows_handle_information(handle)
                )
                after = os.stat(target, follow_symlinks=False)
                if (
                    identity != _status_stable_identity(before)
                    or identity != _status_stable_identity(after)
                    or links != 1
                    or attributes & (0x10 | 0x400)
                    or _is_link_or_reparse(target, after)
                ):
                    raise RunnerError("held Windows file authority is unsafe")
                content = _windows_read_raw_handle(handle, maximum_bytes)
                final_identity, final_size, final_links, final_attributes = (
                    _windows_handle_information(handle)
                )
                _verify_cached_path_proof(target)
                if (
                    len(content) != size
                    or final_identity != identity
                    or final_size != size
                    or final_links != 1
                    or final_attributes & (0x10 | 0x400)
                ):
                    raise RunnerError(
                        "held Windows file changed during read"
                    )
                authority = _HeldRegularFileAuthority(
                    path=target,
                    stable_identity=identity,
                    sha256=_sha256_bytes(content),
                    size_bytes=len(content),
                    posix_descriptor=None,
                    windows_handle=handle,
                )
                yield authority, content
                _verify_cached_path_proof(target)
                _verify_held_regular_file_authority(authority)
            finally:
                _windows_close_raw_handle(handle)
            return

        parent_descriptor = parent_authority.posix_descriptor
        if parent_descriptor is None:
            raise RunnerError("held POSIX parent descriptor is unavailable")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        if delete_access:
            flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        try:
            before = os.stat(
                target.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            descriptor = os.open(
                target.name,
                flags,
                dir_fd=parent_descriptor,
            )
            after = os.stat(
                target.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as error:
            raise RunnerError("unable to open held POSIX file") from error
        try:
            _verify_cached_path_proof(target)
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise RunnerError("held POSIX file authority is unsafe")
            if (
                _status_stable_identity(before)
                != _status_stable_identity(opened)
                or _status_stable_identity(after)
                != _status_stable_identity(opened)
                or _is_link_or_reparse(target, after)
            ):
                raise RunnerError("held POSIX file identity changed during open")
            content = _read_posix_descriptor_bytes(descriptor, maximum_bytes)
            final = os.fstat(descriptor)
            _verify_cached_path_proof(target)
            if (
                _status_stable_identity(final)
                != _status_stable_identity(opened)
                or final.st_size != opened.st_size
                or final.st_nlink != 1
            ):
                raise RunnerError("held POSIX file changed during read")
            authority = _HeldRegularFileAuthority(
                path=target,
                stable_identity=(int(opened.st_dev), int(opened.st_ino)),
                sha256=_sha256_bytes(content),
                size_bytes=len(content),
                posix_descriptor=descriptor,
                windows_handle=None,
            )
            yield authority, content
            _verify_cached_path_proof(target)
            _verify_held_regular_file_authority(authority)
        finally:
            os.close(descriptor)


@contextmanager
def _held_regular_file(
    path: Path,
    *,
    maximum_bytes: int = 268_435_456,
    delete_access: bool = False,
) -> Iterator[_HeldRegularFileAuthority]:
    with _held_regular_file_with_bytes(
        path,
        maximum_bytes=maximum_bytes,
        delete_access=delete_access,
    ) as (authority, _content):
        yield authority


def _read_posix_descriptor_bytes(descriptor: int, maximum_bytes: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = maximum_bytes + 1
    while remaining:
        chunk = os.read(descriptor, min(1_048_576, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    content = b"".join(chunks)
    if len(content) > maximum_bytes:
        raise RunnerError("held file exceeds the allowed size")
    return content


def _read_held_regular_file_bytes(
    authority: _HeldRegularFileAuthority,
    *,
    maximum_bytes: int = 268_435_456,
) -> bytes:
    if type(authority) is not _HeldRegularFileAuthority:
        raise RunnerError("held regular-file authority type changed")
    if os.name == "nt":
        if authority.windows_handle is None or authority.posix_descriptor is not None:
            raise RunnerError("held Windows file handle is unavailable")
        return _windows_read_raw_handle(authority.windows_handle, maximum_bytes)
    if authority.posix_descriptor is None or authority.windows_handle is not None:
        raise RunnerError("held POSIX file descriptor is unavailable")
    return _read_posix_descriptor_bytes(authority.posix_descriptor, maximum_bytes)


def _verify_held_regular_file_metadata(
    authority: _HeldRegularFileAuthority,
    *,
    require_path: bool = True,
) -> None:
    if type(authority) is not _HeldRegularFileAuthority:
        raise RunnerError("held regular-file authority type changed")
    if os.name == "nt":
        assert authority.windows_handle is not None
        identity, size, links, attributes = _windows_handle_information(
            authority.windows_handle
        )
        if (
            identity != authority.stable_identity
            or size != authority.size_bytes
            or links != 1
            or attributes & (0x10 | 0x400)
        ):
            raise RunnerError("held regular-file identity changed")
    else:
        assert authority.posix_descriptor is not None
        opened = os.fstat(authority.posix_descriptor)
        if (
            (int(opened.st_dev), int(opened.st_ino)) != authority.stable_identity
            or opened.st_size != authority.size_bytes
            or opened.st_nlink != 1
        ):
            raise RunnerError("held regular-file identity changed")
    if require_path:
        inspected = os.stat(authority.path, follow_symlinks=False)
        if (
            _is_link_or_reparse(authority.path, inspected)
            or not stat.S_ISREG(inspected.st_mode)
            or inspected.st_nlink != 1
            or _status_stable_identity(inspected) != authority.stable_identity
        ):
            raise RunnerError("held regular-file path changed")


def _verify_held_regular_file_authority(
    authority: _HeldRegularFileAuthority,
    *,
    require_path: bool = True,
) -> None:
    _verify_held_regular_file_metadata(authority, require_path=require_path)
    content = _read_held_regular_file_bytes(authority)
    if (
        len(content) != authority.size_bytes
        or _sha256_bytes(content) != authority.sha256
    ):
        raise RunnerError("held regular-file bytes changed")


def _create_held_regular_file_authority(
    path: Path,
    content: bytes,
    *,
    parent_authority: _HeldDirectoryAuthority,
) -> _HeldRegularFileAuthority:
    target = Path(path)
    if type(content) is not bytes or target.parent != parent_authority.path:
        raise RunnerError("held file creation authority does not match")
    _verify_held_directory_authority(parent_authority)
    if os.path.lexists(target):
        raise RunnerError("held file creation target already exists")
    if os.name != "nt":
        raise RunnerError(
            "POSIX preflight mutation is not qualified; file creation fails closed"
        )
    handle = _windows_open_raw_handle(
        target,
        access=0x80000000 | 0x40000000 | 0x00010000 | 0x00000080,
        share_mode=0x00000001,
        disposition=1,
    )
    try:
        _windows_write_raw_handle(handle, content)
        _windows_flush_raw_handle(handle)
        identity, size, links, attributes = _windows_handle_information(handle)
        inspected = os.stat(target, follow_symlinks=False)
        if (
            identity != _status_stable_identity(inspected)
            or size != len(content)
            or links != 1
            or attributes & (0x10 | 0x400)
            or _is_link_or_reparse(target, inspected)
        ):
            raise RunnerError("new held file identity is unsafe")
        authority = _HeldRegularFileAuthority(
            path=target,
            stable_identity=identity,
            sha256=_sha256_bytes(content),
            size_bytes=len(content),
            posix_descriptor=None,
            windows_handle=handle,
        )
        _verify_held_regular_file_authority(authority)
        _verify_held_directory_authority(parent_authority)
        return authority
    except Exception:
        _windows_close_raw_handle(handle)
        raise


def _open_owned_regular_file_authority(
    path: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
    delete_access: bool,
    maximum_bytes: int = 268_435_456,
) -> _HeldRegularFileAuthority:
    target = Path(path)
    if target.parent != parent_authority.path:
        raise RunnerError("held file open parent authority does not match")
    _verify_held_directory_authority(parent_authority)
    if os.name != "nt":
        raise RunnerError(
            "POSIX preflight mutation is not qualified; file open fails closed"
        )
    before = os.stat(target, follow_symlinks=False)
    if (
        _is_link_or_reparse(target, before)
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
    ):
        raise RunnerError("held file must be regular, no-follow, and single-link")
    access = 0x80000000 | 0x00000080
    if delete_access:
        access |= 0x00010000
    handle = _windows_open_raw_handle(
        target,
        access=access,
        share_mode=0x00000001,
        disposition=3,
    )
    try:
        identity, size, links, attributes = _windows_handle_information(handle)
        after = os.stat(target, follow_symlinks=False)
        content = _windows_read_raw_handle(handle, maximum_bytes)
        if (
            identity != _status_stable_identity(before)
            or identity != _status_stable_identity(after)
            or size != len(content)
            or links != 1
            or attributes & (0x10 | 0x400)
            or _is_link_or_reparse(target, after)
        ):
            raise RunnerError("held file identity changed during open")
        authority = _HeldRegularFileAuthority(
            path=target,
            stable_identity=identity,
            sha256=_sha256_bytes(content),
            size_bytes=len(content),
            posix_descriptor=None,
            windows_handle=handle,
        )
        _verify_held_regular_file_authority(authority)
        return authority
    except Exception:
        _windows_close_raw_handle(handle)
        raise


def _close_owned_regular_file_authority(
    authority: _HeldRegularFileAuthority,
) -> None:
    if os.name == "nt":
        if authority.windows_handle is None:
            raise RunnerError("owned Windows file handle is unavailable")
        _windows_close_raw_handle(authority.windows_handle)
        return
    if authority.posix_descriptor is None:
        raise RunnerError("owned POSIX file descriptor is unavailable")
    os.close(authority.posix_descriptor)


def _close_owned_regular_file_authorities_once(
    authorities: Sequence[_HeldRegularFileAuthority],
) -> Exception | None:
    first_error: Exception | None = None
    seen_handles: set[tuple[str, int]] = set()
    for authority in authorities:
        if type(authority) is not _HeldRegularFileAuthority:
            error = RunnerError("owned regular-file cleanup authority type changed")
            if first_error is None:
                first_error = error
            continue
        if os.name == "nt":
            raw_handle = authority.windows_handle
            handle_kind = "windows"
        else:
            raw_handle = authority.posix_descriptor
            handle_kind = "posix"
        if raw_handle is None:
            error = RunnerError("owned regular-file cleanup handle is unavailable")
            if first_error is None:
                first_error = error
            continue
        handle_key = (handle_kind, int(raw_handle))
        if handle_key in seen_handles:
            error = RunnerError("owned regular-file handle has duplicate cleanup ownership")
            if first_error is None:
                first_error = error
            continue
        seen_handles.add(handle_key)
        try:
            _close_owned_regular_file_authority(authority)
        except Exception as error:
            if first_error is None:
                first_error = error
    return first_error


def _raise_owner_cleanup_failure(
    message: str,
    close_error: Exception,
    *,
    active_error: BaseException | None,
) -> NoReturn:
    classified = RunnerError(message)
    classified.add_note(
        f"owner cleanup error: {type(close_error).__name__}: {close_error}"
    )
    if active_error is not None:
        raise classified from active_error
    raise classified from close_error


def _renamed_held_regular_file_authority(
    authority: _HeldRegularFileAuthority,
    destination: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
) -> _HeldRegularFileAuthority:
    target = Path(destination)
    if target.parent != parent_authority.path:
        raise RunnerError("held rename parent authority does not match")
    if os.name != "nt" or authority.windows_handle is None:
        raise RunnerError("held file rename is qualified only for Windows")
    _verify_held_directory_authority(parent_authority)
    _verify_held_regular_file_authority(authority)
    if os.path.lexists(target):
        raise RunnerError("held file rename target is not absent")
    if parent_authority.windows_handle is None:
        raise RunnerError("held rename directory handle is unavailable")
    _windows_rename_raw_handle(
        authority.windows_handle,
        target.name,
        destination_parent_handle=parent_authority.windows_handle,
    )
    _verify_held_directory_authority(parent_authority)
    renamed = _HeldRegularFileAuthority(
        path=target,
        stable_identity=authority.stable_identity,
        sha256=authority.sha256,
        size_bytes=authority.size_bytes,
        posix_descriptor=None,
        windows_handle=authority.windows_handle,
    )
    _verify_held_regular_file_authority(renamed)
    _verify_held_directory_authority(parent_authority)
    return renamed


def _retargeted_held_regular_file_authority(
    authority: _HeldRegularFileAuthority,
    path: Path,
) -> _HeldRegularFileAuthority:
    retargeted = _HeldRegularFileAuthority(
        path=Path(path),
        stable_identity=authority.stable_identity,
        sha256=authority.sha256,
        size_bytes=authority.size_bytes,
        posix_descriptor=authority.posix_descriptor,
        windows_handle=authority.windows_handle,
    )
    _verify_held_regular_file_authority(retargeted)
    return retargeted


def _unlink_held_regular_file_authority(
    authority: _HeldRegularFileAuthority,
) -> None:
    if os.name != "nt" or authority.windows_handle is None:
        raise RunnerError("held file unlink is qualified only for Windows")
    _verify_held_regular_file_authority(authority)
    _windows_unlink_raw_handle(authority.windows_handle)


def _directory_barrier_authority(
    authority: _HeldDirectoryAuthority,
) -> _DirectoryAuthority:
    _verify_held_directory_authority(authority)
    return _DirectoryAuthority(
        path=authority.path,
        posix_descriptor=authority.posix_descriptor,
        windows_handle=authority.windows_handle,
    )


def _flush_held_directory(authority: _HeldDirectoryAuthority) -> None:
    _sync_directory(
        authority.path,
        authority=_directory_barrier_authority(authority),
    )
    _verify_held_directory_authority(authority)


@contextmanager
def _held_state_root_authority(
    paths: RunnerPaths,
) -> Iterator[_HeldDirectoryAuthority]:
    project_root = _absolute_lexical(
        Path(paths.project_root),
        Path(paths.project_root),
    )
    state_root = _absolute_lexical(Path(paths.state_root), project_root)
    try:
        relative_parts = state_root.relative_to(project_root).parts
    except ValueError as error:  # pragma: no cover - layout already rejects it
        raise RunnerError("state root is outside the project") from error
    if not relative_parts:
        raise RunnerError("state root cannot equal the project root")

    with ExitStack() as stack:
        parent = stack.enter_context(_held_directory_authority(project_root))
        cursor = project_root
        for component in relative_parts:
            cursor /= component
            parent = stack.enter_context(
                _held_child_directory_authority(cursor, parent)
            )
        if parent.path != state_root:
            raise RunnerError("held state-root path changed")
        yield parent


def _held_directory_entry_statuses(
    authority: _HeldDirectoryAuthority,
) -> dict[str, os.stat_result]:
    _verify_held_directory_authority(authority)
    try:
        with os.scandir(authority.path) as entries:
            result = {
                entry.name: os.stat(
                    authority.path / entry.name,
                    follow_symlinks=False,
                )
                for entry in entries
            }
    except OSError as error:
        raise RunnerError("unable to enumerate held directory") from error
    _verify_held_directory_authority(authority)
    return result


def _require_safe_regular_entry(
    parent: _HeldDirectoryAuthority,
    name: str,
    status: os.stat_result,
) -> None:
    path = parent.path / name
    if (
        _is_link_or_reparse(path, status)
        or not stat.S_ISREG(status.st_mode)
        or status.st_nlink != 1
    ):
        raise RunnerError(f"unsafe regular entry in held directory: {name}")


def _require_safe_directory_entry(
    parent: _HeldDirectoryAuthority,
    name: str,
    status: os.stat_result,
) -> None:
    path = parent.path / name
    if _is_link_or_reparse(path, status) or not stat.S_ISDIR(status.st_mode):
        raise RunnerError(f"unsafe directory entry in held directory: {name}")


def _state_replacement_paths(paths: RunnerPaths) -> tuple[Path, Path]:
    return _replacement_control_paths(paths.state_path)


def _non_lockbox_state_root_entry_policy(
    paths: RunnerPaths,
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    intent_path, prior_path = _state_replacement_paths(paths)
    regular_names = frozenset({
        MATERIAL_PIPELINE_LOCK_NAME,
        "state.json",
    })
    control_names = frozenset({
        paths.preflight_state_stage_path.name,
        intent_path.name,
        prior_path.name,
        paths.non_lockbox_state_stage_path.name,
        paths.non_lockbox_state_intent_path.name,
        paths.non_lockbox_state_prior_path.name,
    })
    directory_names = frozenset({
        "inputs",
        "split",
        "preflight",
        "non-lockbox",
        "dependencies",
        "resolver-venv",
        "venv",
    })
    canonical_names = (
        regular_names
        | control_names
        | directory_names
        | OPAQUE_POST_NON_LOCKBOX_STATE_ROOT_ENTRY_NAMES
    )
    normalized_names = {
        name.rstrip(" .").casefold() for name in canonical_names
    }
    if len(normalized_names) != len(canonical_names):
        raise RunnerError("canonical state-root entry names collide")
    return regular_names, control_names, directory_names


def _classify_non_lockbox_state_root_entry_names(
    paths: RunnerPaths,
    names: tuple[str, ...],
    *,
    allow_state_controls: bool,
) -> tuple[str, ...]:
    if type(names) is not tuple or type(allow_state_controls) is not bool:
        raise RunnerError("state-root entry-name classifier input changed")
    regular_names, control_names, directory_names = (
        _non_lockbox_state_root_entry_policy(paths)
    )
    admitted_names = regular_names | control_names | directory_names
    canonical_names = admitted_names | OPAQUE_POST_NON_LOCKBOX_STATE_ROOT_ENTRY_NAMES
    canonical_by_normalized_name = {
        name.rstrip(" .").casefold(): name for name in canonical_names
    }
    seen_normalized_names: set[str] = set()
    admitted: list[str] = []
    for name in names:
        if type(name) is not str or not name:
            raise RunnerError("state-root entry name is invalid")
        normalized_name = name.rstrip(" .").casefold()
        if normalized_name in seen_normalized_names:
            raise RunnerError("duplicate normalized state-root entry name")
        seen_normalized_names.add(normalized_name)
        if name in OPAQUE_POST_NON_LOCKBOX_STATE_ROOT_ENTRY_NAMES:
            continue
        if name in admitted_names:
            if not allow_state_controls and name in control_names:
                raise RunnerError("unexpected state replacement control entry")
            admitted.append(name)
            continue
        if normalized_name in canonical_by_normalized_name:
            raise RunnerError("noncanonical state-root entry name")
        raise RunnerError(
            f"unknown state-root allowlist entry is retained: {name}"
        )
    return tuple(admitted)


def _held_non_lockbox_state_root_entry_statuses(
    paths: RunnerPaths,
    authority: _HeldDirectoryAuthority,
    *,
    allow_state_controls: bool,
) -> dict[str, os.stat_result]:
    _verify_held_directory_authority(authority)
    try:
        with os.scandir(authority.path) as entries:
            names = tuple(entry.name for entry in entries)
    except OSError as error:
        raise RunnerError("unable to enumerate held state root") from error
    admitted_names = _classify_non_lockbox_state_root_entry_names(
        paths,
        names,
        allow_state_controls=allow_state_controls,
    )
    try:
        result = {
            name: os.stat(
                authority.path / name,
                follow_symlinks=False,
            )
            for name in admitted_names
        }
    except OSError as error:
        raise RunnerError("unable to inspect admitted state-root entry") from error
    _verify_held_directory_authority(authority)
    return result


def _validated_state_root_allowlist_snapshot(
    paths: RunnerPaths,
    authority: _HeldDirectoryAuthority,
    *,
    allow_state_controls: bool,
) -> frozenset[str]:
    regular_names, control_names, directory_names = (
        _non_lockbox_state_root_entry_policy(paths)
    )
    entries = _held_non_lockbox_state_root_entry_statuses(
        paths,
        authority,
        allow_state_controls=allow_state_controls,
    )
    unknown = set(entries) - regular_names - control_names - directory_names
    if unknown:
        raise RunnerError(
            "unknown state-root allowlist entry is retained: "
            + ", ".join(sorted(unknown))
        )
    for name, status in entries.items():
        if name in directory_names:
            _require_safe_directory_entry(authority, name, status)
        else:
            _require_safe_regular_entry(authority, name, status)
    return frozenset(set(entries) & control_names)


def _validate_state_root_allowlist(
    paths: RunnerPaths,
    authority: _HeldDirectoryAuthority,
    *,
    allow_state_controls: bool,
) -> frozenset[str]:
    return _validated_state_root_allowlist_snapshot(
        paths,
        authority,
        allow_state_controls=allow_state_controls,
    )


def _validated_state_root_controls(
    paths: RunnerPaths,
    authority: _HeldDirectoryAuthority,
    *,
    allow_state_controls: bool,
) -> frozenset[str]:
    present_controls = _validate_state_root_allowlist(
        paths,
        authority,
        allow_state_controls=allow_state_controls,
    )
    if present_controls is None:
        present_controls = _validated_state_root_allowlist_snapshot(
            paths,
            authority,
            allow_state_controls=allow_state_controls,
        )
    if type(present_controls) is not frozenset:
        raise RunnerError("state-root allowlist control snapshot type changed")
    return present_controls


def _state_control_name_families(
    paths: RunnerPaths,
) -> tuple[frozenset[str], frozenset[str]]:
    preflight_intent, preflight_prior = _state_replacement_paths(paths)
    preflight = frozenset(
        {
            paths.preflight_state_stage_path.name,
            preflight_intent.name,
            preflight_prior.name,
        }
    )
    non_lockbox = frozenset(
        {
            paths.non_lockbox_state_stage_path.name,
            paths.non_lockbox_state_intent_path.name,
            paths.non_lockbox_state_prior_path.name,
        }
    )
    if preflight & non_lockbox:
        raise RunnerError("state replacement control family names overlap")
    return preflight, non_lockbox


def _reject_mixed_state_control_families(
    paths: RunnerPaths,
    present_controls: frozenset[str],
) -> None:
    preflight, non_lockbox = _state_control_name_families(paths)
    if present_controls & preflight and present_controls & non_lockbox:
        raise RunnerError("mixed state replacement control families are retained")


def _validate_exact_state_control_family(
    paths: RunnerPaths,
    present_controls: frozenset[str],
    *,
    family: Literal["preflight", "non_lockbox"],
    include_prior: bool,
) -> None:
    preflight, non_lockbox = _state_control_name_families(paths)
    if family == "preflight":
        intent_path, prior_path = _state_replacement_paths(paths)
        expected = {
            paths.preflight_state_stage_path.name,
            intent_path.name,
        }
        if include_prior:
            expected.add(prior_path.name)
    else:
        expected = {
            paths.non_lockbox_state_stage_path.name,
            paths.non_lockbox_state_intent_path.name,
        }
        if include_prior:
            expected.add(paths.non_lockbox_state_prior_path.name)
    if present_controls != frozenset(expected):
        other = non_lockbox if family == "preflight" else preflight
        if present_controls & other:
            raise RunnerError(
                f"{family} transaction found the wrong state control family"
            )
        raise RunnerError(f"{family} state control family shape changed")


def _lock_file_identity(handle: BinaryIO) -> tuple[int, ...]:
    descriptor = handle.fileno()
    if os.name == "nt":
        return _windows_handle_information(msvcrt.get_osfhandle(descriptor))[0]
    opened = os.fstat(descriptor)
    return (int(opened.st_dev), int(opened.st_ino))


def _open_material_lock_handle(
    path: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
) -> BinaryIO:
    if Path(path).parent != parent_authority.path:
        raise RunnerError("material lock parent authority does not match")
    _verify_held_directory_authority(parent_authority)
    exists = os.path.lexists(path)
    before = os.stat(path, follow_symlinks=False) if exists else None
    if before is not None and (
        _is_link_or_reparse(path, before)
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
    ):
        raise RunnerError("material-pipeline lock is unsafe")
    try:
        if os.name == "nt":
            descriptor = _windows_open_mutation_fd(
                path,
                access=0x80000000 | 0x40000000 | 0x00000080,
                disposition=3 if exists else 1,
                descriptor_flags=os.O_RDWR | getattr(os, "O_BINARY", 0),
                share_mode=0x00000001,
            )
        else:
            flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            flags |= os.O_CREAT | os.O_EXCL if not exists else 0
            descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise RunnerError("unable to open material-pipeline lock") from error
    try:
        opened = os.fstat(descriptor)
        after = os.stat(path, follow_symlinks=False)
        if (
            _is_link_or_reparse(path, after)
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or _status_stable_identity(opened)
            != _status_stable_identity(after)
            or (
                before is not None
                and _status_stable_identity(before)
                != _status_stable_identity(opened)
            )
        ):
            raise RunnerError("material-pipeline lock identity changed")
        return os.fdopen(descriptor, "r+b", closefd=True)
    except Exception:
        os.close(descriptor)
        raise


def _verify_material_pipeline_authority(
    authority: _MaterialPipelineAuthority,
) -> None:
    if type(authority) is not _MaterialPipelineAuthority:
        raise RunnerError("material-pipeline authority type changed")
    _verify_held_directory_authority(authority.state_root)
    if authority.lock_file.closed:
        raise RunnerError("material-pipeline lock handle is closed")
    if _lock_file_identity(authority.lock_file) != authority.lock_stable_identity:
        raise RunnerError("material-pipeline lock identity changed")
    status = os.stat(authority.lock_path, follow_symlinks=False)
    if (
        _is_link_or_reparse(authority.lock_path, status)
        or not stat.S_ISREG(status.st_mode)
        or status.st_nlink != 1
        or _status_stable_identity(status) != authority.lock_stable_identity
    ):
        raise RunnerError("material-pipeline lock path changed")


@contextmanager
def material_pipeline_lock(
    paths: RunnerPaths,
) -> Iterator[_MaterialPipelineAuthority]:
    _validate_layout(paths)
    with _held_state_root_authority(paths) as state_root:
        lock_path = Path(paths.material_pipeline_lock_path)
        lock_file = _open_material_lock_handle(
            lock_path,
            parent_authority=state_root,
        )
        acquired = False
        try:
            try:
                _acquire_os_lock(lock_file)
            except OSError as error:
                raise RunnerError(
                    "material-pipeline lock is already held or unavailable"
                ) from error
            acquired = True
            authority = _MaterialPipelineAuthority(
                state_root=state_root,
                lock_path=lock_path,
                lock_stable_identity=_lock_file_identity(lock_file),
                lock_file=lock_file,
            )
            _verify_material_pipeline_authority(authority)
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=True,
            )
            yield authority
            _verify_material_pipeline_authority(authority)
        finally:
            active_error = sys.exc_info()[1]
            cleanup_errors: list[tuple[str, OSError]] = []
            if acquired:
                try:
                    _release_os_lock(lock_file)
                except OSError as error:
                    cleanup_errors.append(("release", error))
            try:
                lock_file.close()
            except OSError as error:
                cleanup_errors.append(("close", error))
            if cleanup_errors:
                classified = RunnerError("material-pipeline lock cleanup failed")
                for operation, error in cleanup_errors:
                    classified.add_note(
                        "material-pipeline lock "
                        f"{operation} error: {type(error).__name__}: {error}"
                    )
                if active_error is not None:
                    raise classified from active_error
                raise classified from cleanup_errors[0][1]


def _preflight_artifact_destinations(paths: RunnerPaths) -> tuple[Path, ...]:
    return (
        Path(paths.input_ledger_path),
        Path(paths.split_manifest_path),
        *(Path(paths.partition_authority_cache_path(role)) for role in NONFINAL_PARTITION_ROLES),
    )


def _artifact_stage_path(destination: Path) -> Path:
    target = Path(destination)
    return target.with_name(f".{target.name}.preflight.stage")


def _output_parent_for_destination(
    paths: RunnerPaths,
    destination: Path,
    authorities: _PreflightOutputAuthorities,
) -> _HeldDirectoryAuthority:
    target = Path(destination)
    if target == Path(paths.input_ledger_path):
        parent = authorities.inputs_root
    elif target == Path(paths.split_manifest_path):
        parent = authorities.split_root
    elif target in {
        Path(paths.partition_authority_cache_path(role))
        for role in NONFINAL_PARTITION_ROLES
    }:
        parent = authorities.preflight_root
    else:
        raise RunnerError("preflight artifact destination is not fixed")
    if target.parent != parent.path:
        raise RunnerError("preflight artifact parent authority changed")
    _verify_held_directory_authority(parent)
    return parent


def _safe_unlink_owned_file(authority: _HeldRegularFileAuthority) -> None:
    unlink_error: Exception | None = None
    try:
        _unlink_held_regular_file_authority(authority)
    except Exception as error:
        unlink_error = error
    try:
        _close_owned_regular_file_authority(authority)
    except Exception:
        if unlink_error is None:
            raise
    if unlink_error is not None:
        raise unlink_error


def _recover_preflight_artifact_destination(
    destination: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
) -> None:
    target = Path(destination)
    if target.parent != parent_authority.path:
        raise RunnerError("artifact recovery parent authority changed")
    stage_path = _artifact_stage_path(target)
    intent_path, prior_path = _replacement_control_paths(target)
    _verify_held_directory_authority(parent_authority)

    intent_exists = os.path.lexists(intent_path)
    prior_exists = os.path.lexists(prior_path)
    stage_exists = os.path.lexists(stage_path)
    if not intent_exists:
        if prior_exists:
            raise RunnerError("orphaned preflight replacement prior is retained")
        if stage_exists:
            stage = _open_owned_regular_file_authority(
                stage_path,
                parent_authority=parent_authority,
                delete_access=True,
            )
            owned_stage = stage
            stage = None
            _safe_unlink_owned_file(owned_stage)
            _flush_held_directory(parent_authority)
        return

    intent_file = _open_owned_regular_file_authority(
        intent_path,
        parent_authority=parent_authority,
        delete_access=True,
    )
    try:
        intent = _validate_replacement_intent(
            _load_json_object_bytes(
                _read_held_regular_file_bytes(intent_file),
                "preflight artifact replacement intent",
            ),
            destination=target,
            prior_path=prior_path,
        )
        destination_file = (
            _open_owned_regular_file_authority(
                target,
                parent_authority=parent_authority,
                delete_access=True,
            )
            if os.path.lexists(target)
            else None
        )
        prior_file = (
            _open_owned_regular_file_authority(
                prior_path,
                parent_authority=parent_authority,
                delete_access=True,
            )
            if prior_exists
            else None
        )
        stage_file = (
            _open_owned_regular_file_authority(
                stage_path,
                parent_authority=parent_authority,
                delete_access=True,
            )
            if stage_exists
            else None
        )
        try:
            if (
                destination_file is not None
                and destination_file.sha256 == intent["source_sha256"]
                and stage_file is None
            ):
                if prior_file is not None:
                    if prior_file.sha256 != intent["prior_sha256"]:
                        raise RunnerError("artifact recovery prior digest mismatch")
                    owned_prior = prior_file
                    prior_file = None
                    _safe_unlink_owned_file(owned_prior)
            elif (
                destination_file is None
                and prior_file is not None
                and stage_file is not None
                and prior_file.sha256 == intent["prior_sha256"]
                and stage_file.sha256 == intent["source_sha256"]
            ):
                restored = _renamed_held_regular_file_authority(
                    prior_file,
                    target,
                    parent_authority=parent_authority,
                )
                prior_file = restored
                owned_stage = stage_file
                stage_file = None
                _safe_unlink_owned_file(owned_stage)
            elif (
                destination_file is not None
                and destination_file.sha256 == intent["prior_sha256"]
                and prior_file is None
                and stage_file is not None
                and stage_file.sha256 == intent["source_sha256"]
            ):
                owned_stage = stage_file
                stage_file = None
                _safe_unlink_owned_file(owned_stage)
            else:
                raise RunnerError(
                    "preflight artifact recovery is ambiguous; evidence retained"
                )
        finally:
            for held in (destination_file, prior_file, stage_file):
                if held is not None:
                    _close_owned_regular_file_authority(held)
        owned_intent = intent_file
        intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent_authority)
    finally:
        if intent_file is not None:
            _close_owned_regular_file_authority(intent_file)


def _preflight_recovery_plan_files(
    plan: _PreflightArtifactRecoveryPlan,
) -> tuple[_HeldRegularFileAuthority, ...]:
    return tuple(
        authority
        for authority in (
            plan.destination_file,
            plan.intent_file,
            plan.prior_file,
            plan.stage_file,
        )
        if authority is not None
    )


def _close_preflight_artifact_recovery_plan(
    plan: _PreflightArtifactRecoveryPlan,
) -> None:
    authorities = _preflight_recovery_plan_files(plan)
    plan.destination_file = None
    plan.intent_file = None
    plan.prior_file = None
    plan.stage_file = None
    cleanup_error = _close_owned_regular_file_authorities_once(authorities)
    if cleanup_error is not None:
        raise cleanup_error


def _plan_preflight_artifact_destination_recovery(
    destination: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
    entry_names: frozenset[str],
) -> _PreflightArtifactRecoveryPlan:
    target = Path(destination)
    if target.parent != parent_authority.path:
        raise RunnerError("artifact recovery parent authority changed")
    stage_path = _artifact_stage_path(target)
    intent_path, prior_path = _replacement_control_paths(target)
    recognized_names = {
        target.name,
        stage_path.name,
        intent_path.name,
        prior_path.name,
    }
    if not entry_names <= recognized_names:
        raise RunnerError("artifact recovery plan received an unknown entry")

    opened: list[_HeldRegularFileAuthority] = []

    def open_if_present(path: Path) -> _HeldRegularFileAuthority | None:
        if path.name not in entry_names:
            return None
        authority = _open_owned_regular_file_authority(
            path,
            parent_authority=parent_authority,
            delete_access=True,
        )
        opened.append(authority)
        return authority

    try:
        destination_file = open_if_present(target)
        intent_file = open_if_present(intent_path)
        prior_file = open_if_present(prior_path)
        stage_file = open_if_present(stage_path)
        if intent_file is None:
            if prior_file is not None:
                raise RunnerError("orphaned preflight replacement prior is retained")
            action = "discard-stage" if stage_file is not None else "none"
        else:
            intent = _validate_replacement_intent(
                _load_json_object_bytes(
                    _read_held_regular_file_bytes(intent_file),
                    "preflight artifact replacement intent",
                ),
                destination=target,
                prior_path=prior_path,
            )
            if (
                destination_file is not None
                and destination_file.sha256 == intent["source_sha256"]
                and stage_file is None
            ):
                if (
                    prior_file is not None
                    and prior_file.sha256 != intent["prior_sha256"]
                ):
                    raise RunnerError("artifact recovery prior digest mismatch")
                action = "finish-committed"
            elif (
                destination_file is None
                and prior_file is not None
                and stage_file is not None
                and prior_file.sha256 == intent["prior_sha256"]
                and stage_file.sha256 == intent["source_sha256"]
            ):
                action = "restore-prior"
            elif (
                destination_file is not None
                and destination_file.sha256 == intent["prior_sha256"]
                and prior_file is None
                and stage_file is not None
                and stage_file.sha256 == intent["source_sha256"]
            ):
                action = "discard-uncommitted-stage"
            else:
                raise RunnerError(
                    "preflight artifact recovery is ambiguous; evidence retained"
                )
        plan = _PreflightArtifactRecoveryPlan(
            destination=target,
            parent_authority=parent_authority,
            action=action,
            destination_file=destination_file,
            intent_file=intent_file,
            prior_file=prior_file,
            stage_file=stage_file,
        )
        opened.clear()
        return plan
    finally:
        cleanup_error = _close_owned_regular_file_authorities_once(opened)
        if cleanup_error is not None:
            raise cleanup_error


def _plan_preflight_artifact_recovery(
    paths: RunnerPaths,
    authorities: _PreflightOutputAuthorities,
) -> tuple[_PreflightArtifactRecoveryPlan, ...]:
    destinations = _preflight_artifact_destinations(paths)
    groups = (
        (authorities.inputs_root, destinations[:1]),
        (authorities.split_root, destinations[1:2]),
        (authorities.preflight_root, destinations[2:]),
    )
    entry_names_by_parent: dict[Path, frozenset[str]] = {}
    destination_names_by_parent: dict[Path, dict[Path, frozenset[str]]] = {}
    for parent, fixed_destinations in groups:
        fixed_names = {path.name for path in fixed_destinations}
        control_names: set[str] = set()
        names_for_destination: dict[Path, frozenset[str]] = {}
        entries = _held_directory_entry_statuses(parent)
        for destination in fixed_destinations:
            intent, prior = _replacement_control_paths(destination)
            recognized = frozenset(
                {
                    destination.name,
                    _artifact_stage_path(destination).name,
                    intent.name,
                    prior.name,
                }
            )
            names_for_destination[destination] = frozenset(set(entries) & recognized)
            control_names.update(recognized - {destination.name})
        unknown = set(entries) - fixed_names - control_names
        if unknown:
            raise RunnerError(
                "unknown preflight output shape entry is retained: "
                + ", ".join(sorted(unknown))
            )
        for name, status in entries.items():
            _require_safe_regular_entry(parent, name, status)
        entry_names_by_parent[parent.path] = frozenset(entries)
        destination_names_by_parent[parent.path] = names_for_destination

    plans: list[_PreflightArtifactRecoveryPlan] = []
    try:
        for destination in destinations:
            parent = _output_parent_for_destination(paths, destination, authorities)
            plans.append(
                _plan_preflight_artifact_destination_recovery(
                    destination,
                    parent_authority=parent,
                    entry_names=destination_names_by_parent[parent.path][destination],
                )
            )
        planned_files = tuple(
            authority
            for plan in plans
            for authority in _preflight_recovery_plan_files(plan)
        )
        for parent, _fixed_destinations in groups:
            current_entries = _held_directory_entry_statuses(parent)
            if frozenset(current_entries) != entry_names_by_parent[parent.path]:
                raise RunnerError(
                    "preflight output recovery namespace changed during planning"
                )
        if {authority.path for authority in planned_files} != {
            parent.path / name
            for parent, _fixed_destinations in groups
            for name in entry_names_by_parent[parent.path]
        }:
            raise RunnerError("preflight output recovery plan is incomplete")
        for authority in planned_files:
            _verify_held_regular_file_authority(authority)
        return tuple(plans)
    except Exception:
        cleanup_error: Exception | None = None
        for plan in plans:
            try:
                _close_preflight_artifact_recovery_plan(plan)
            except Exception as error:
                if cleanup_error is None:
                    cleanup_error = error
        if cleanup_error is not None:
            raise cleanup_error
        raise


def _execute_preflight_artifact_recovery_plan(
    plan: _PreflightArtifactRecoveryPlan,
) -> None:
    parent = plan.parent_authority
    _verify_held_directory_authority(parent)
    for authority in _preflight_recovery_plan_files(plan):
        _verify_held_regular_file_authority(authority)
    if plan.action == "discard-stage":
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
        _flush_held_directory(parent)
    elif plan.action == "finish-committed":
        if plan.prior_file is not None:
            owned_prior = plan.prior_file
            plan.prior_file = None
            _safe_unlink_owned_file(owned_prior)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent)
    elif plan.action == "restore-prior":
        assert plan.prior_file is not None
        restored = _renamed_held_regular_file_authority(
            plan.prior_file,
            plan.destination,
            parent_authority=parent,
        )
        plan.prior_file = restored
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent)
    elif plan.action == "discard-uncommitted-stage":
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent)
    elif plan.action != "none":
        raise RunnerError("preflight artifact recovery plan action changed")


def _verify_preflight_artifact_recovery_plans(
    paths: RunnerPaths,
    authorities: _PreflightOutputAuthorities,
    plans: tuple[_PreflightArtifactRecoveryPlan, ...],
) -> None:
    destinations = _preflight_artifact_destinations(paths)
    if (
        type(plans) is not tuple
        or len(plans) != len(destinations)
        or any(
            type(plan) is not _PreflightArtifactRecoveryPlan
            or plan.destination != destination
            for plan, destination in zip(plans, destinations, strict=True)
        )
    ):
        raise RunnerError("preflight artifact recovery plan order changed")
    held_roots = (
        authorities.inputs_root,
        authorities.split_root,
        authorities.preflight_root,
    )
    expected_names = {root.path: set() for root in held_roots}
    for plan in plans:
        expected_parent = _output_parent_for_destination(
            paths,
            plan.destination,
            authorities,
        )
        if plan.parent_authority is not expected_parent:
            raise RunnerError("preflight artifact recovery plan parent changed")
        for authority in _preflight_recovery_plan_files(plan):
            if authority.path.parent != expected_parent.path:
                raise RunnerError("preflight recovery file parent changed")
            expected_names[expected_parent.path].add(authority.path.name)
            _verify_held_regular_file_authority(authority)
    for parent in held_roots:
        entries = _held_directory_entry_statuses(parent)
        if set(entries) != expected_names[parent.path]:
            raise RunnerError(
                "preflight output recovery namespace changed before execution"
            )
        for name, status in entries.items():
            _require_safe_regular_entry(parent, name, status)


def _validate_preflight_output_shape(
    paths: RunnerPaths,
    authorities: _PreflightOutputAuthorities,
    *,
    require_complete: bool,
    allow_controls: bool,
) -> None:
    destinations = _preflight_artifact_destinations(paths)
    groups = (
        (authorities.inputs_root, destinations[:1]),
        (authorities.split_root, destinations[1:2]),
        (authorities.preflight_root, destinations[2:]),
    )
    for parent, fixed_destinations in groups:
        fixed_names = {path.name for path in fixed_destinations}
        control_names: set[str] = set()
        for destination in fixed_destinations:
            intent, prior = _replacement_control_paths(destination)
            control_names.update(
                {_artifact_stage_path(destination).name, intent.name, prior.name}
            )
        entries = _held_directory_entry_statuses(parent)
        unknown = set(entries) - fixed_names - control_names
        if unknown:
            raise RunnerError(
                "unknown preflight output shape entry is retained: "
                + ", ".join(sorted(unknown))
            )
        if not allow_controls and set(entries) & control_names:
            raise RunnerError("preflight output recovery control remains")
        if require_complete and set(entries) != fixed_names:
            raise RunnerError("preflight output shape is incomplete")
        for name, status in entries.items():
            _require_safe_regular_entry(parent, name, status)


@contextmanager
def _held_preflight_output_authorities(
    paths: RunnerPaths,
    material_authority: _MaterialPipelineAuthority,
) -> Iterator[_PreflightOutputAuthorities]:
    if type(material_authority) is not _MaterialPipelineAuthority:
        raise RunnerError("material-pipeline authority is required")
    _verify_material_pipeline_authority(material_authority)
    state_root = material_authority.state_root
    with ExitStack() as stack:
        held: list[_HeldDirectoryAuthority] = []
        for path in (
            Path(paths.input_ledger_path).parent,
            Path(paths.split_manifest_path).parent,
            Path(paths.preflight_cache_root),
        ):
            held.append(
                stack.enter_context(
                    _held_child_directory_authority(path, state_root)
                )
            )
        authorities = _PreflightOutputAuthorities(*held)
        recovery_plans = _plan_preflight_artifact_recovery(paths, authorities)
        try:
            _verify_preflight_artifact_recovery_plans(
                paths,
                authorities,
                recovery_plans,
            )
            for recovery_plan in recovery_plans:
                _execute_preflight_artifact_recovery_plan(recovery_plan)
        finally:
            cleanup_error: Exception | None = None
            for recovery_plan in recovery_plans:
                try:
                    _close_preflight_artifact_recovery_plan(recovery_plan)
                except Exception as error:
                    if cleanup_error is None:
                        cleanup_error = error
            if cleanup_error is not None:
                raise cleanup_error
        _validate_preflight_output_shape(
            paths,
            authorities,
            require_complete=False,
            allow_controls=False,
        )
        try:
            yield authorities
        except Exception:
            for authority in held:
                _verify_held_directory_authority(authority)
            raise
        _validate_preflight_output_shape(
            paths,
            authorities,
            require_complete=True,
            allow_controls=False,
        )
        _validate_state_root_allowlist(
            paths,
            state_root,
            allow_state_controls=True,
        )


def _replace_preflight_bytes_durably(
    paths: RunnerPaths,
    destination: Path,
    content: bytes,
    *,
    output_authorities: _PreflightOutputAuthorities,
) -> None:
    target = Path(destination)
    if (
        type(paths) is not RunnerPaths
        or type(content) is not bytes
        or target not in _preflight_artifact_destinations(paths)
        or type(output_authorities) is not _PreflightOutputAuthorities
    ):
        raise RunnerError("artifact-only preflight replacement target is invalid")
    expected_roots = (
        Path(paths.input_ledger_path).parent,
        Path(paths.split_manifest_path).parent,
        Path(paths.preflight_cache_root),
    )
    held_roots = (
        output_authorities.inputs_root,
        output_authorities.split_root,
        output_authorities.preflight_root,
    )
    if any(
        type(authority) is not _HeldDirectoryAuthority
        or authority.path != expected
        for authority, expected in zip(held_roots, expected_roots, strict=True)
    ):
        raise RunnerError("preflight output capability does not match paths")
    for authority in held_roots:
        _verify_held_directory_authority(authority)
    parent_authority = _output_parent_for_destination(
        paths,
        target,
        output_authorities,
    )
    _validate_preflight_output_shape(
        paths,
        output_authorities,
        require_complete=False,
        allow_controls=False,
    )
    if os.name != "nt":
        raise RunnerError("preflight durable replacement is Windows-qualified only")

    _recover_preflight_artifact_destination(
        target,
        parent_authority=parent_authority,
    )
    stage_path = _artifact_stage_path(target)
    intent_path, prior_path = _replacement_control_paths(target)
    stage = _create_held_regular_file_authority(
        stage_path,
        content,
        parent_authority=parent_authority,
    )
    promoted: _HeldRegularFileAuthority | None = stage
    previous: _HeldRegularFileAuthority | None = None
    intent: _HeldRegularFileAuthority | None = None
    try:
        if os.path.lexists(target):
            if os.path.lexists(intent_path) or os.path.lexists(prior_path):
                raise RunnerError("preflight replacement control entry already exists")
            previous = _open_owned_regular_file_authority(
                target,
                parent_authority=parent_authority,
                delete_access=True,
            )
            intent_payload = {
                "schema_version": _REPLACE_INTENT_SCHEMA_VERSION,
                "destination_name": target.name,
                "prior_name": prior_path.name,
                "source_sha256": stage.sha256,
                "prior_sha256": previous.sha256,
            }
            intent = _create_held_regular_file_authority(
                intent_path,
                canonical_json_bytes(intent_payload),
                parent_authority=parent_authority,
            )
            previous = _renamed_held_regular_file_authority(
                previous,
                prior_path,
                parent_authority=parent_authority,
            )
        promoted = _renamed_held_regular_file_authority(
            stage,
            target,
            parent_authority=parent_authority,
        )
        _flush_held_directory(parent_authority)
        _verify_held_regular_file_authority(promoted)
        if _read_held_regular_file_bytes(promoted) != content:
            raise RunnerError("preflight artifact immediate readback mismatch")
        if previous is not None:
            owned_previous = previous
            previous = None
            _safe_unlink_owned_file(owned_previous)
        if intent is not None:
            owned_intent = intent
            intent = None
            _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent_authority)
        _verify_held_regular_file_authority(promoted)
    finally:
        if previous is not None:
            _close_owned_regular_file_authority(previous)
        if intent is not None:
            _close_owned_regular_file_authority(intent)
        if promoted is not None:
            _close_owned_regular_file_authority(promoted)


_STATE_REPLACEMENT_INTENT_FIELDS = frozenset(
    {
        "schema_version",
        "destination_name",
        "stage_name",
        "prior_name",
        "admission",
        "stage_stable_identity",
        "stage_sha256",
        "stage_size_bytes",
        "initial_stable_identity",
        "initial_sha256",
        "initial_size_bytes",
    }
)


def _state_replacement_intent_payload(
    paths: RunnerPaths,
    *,
    stage: _HeldRegularFileAuthority,
    admitted: _AdmittedStateAuthority,
) -> dict[str, Any]:
    _validate_digest(stage.sha256, "state stage")
    intent_path, prior_path = _state_replacement_paths(paths)
    del intent_path
    initial = admitted.initial_file
    return {
        "schema_version": _REPLACE_INTENT_SCHEMA_VERSION,
        "destination_name": paths.state_path.name,
        "stage_name": paths.preflight_state_stage_path.name,
        "prior_name": prior_path.name,
        "admission": admitted.admission,
        "stage_stable_identity": list(stage.stable_identity),
        "stage_sha256": stage.sha256,
        "stage_size_bytes": stage.size_bytes,
        "initial_stable_identity": (
            list(initial.stable_identity) if initial is not None else None
        ),
        "initial_sha256": initial.sha256 if initial is not None else None,
        "initial_size_bytes": initial.size_bytes if initial is not None else None,
    }


def _validate_state_replacement_intent(
    payload: Any,
    paths: RunnerPaths,
) -> dict[str, Any]:
    _intent_path, prior_path = _state_replacement_paths(paths)
    if not isinstance(payload, dict) or set(payload) != _STATE_REPLACEMENT_INTENT_FIELDS:
        raise RunnerError("invalid preflight state intent fields")
    if (
        type(payload["schema_version"]) is not int
        or payload["schema_version"] != _REPLACE_INTENT_SCHEMA_VERSION
        or payload["destination_name"] != paths.state_path.name
        or payload["stage_name"] != paths.preflight_state_stage_path.name
        or payload["prior_name"] != prior_path.name
        or payload["admission"] not in {"absent", "initialized"}
    ):
        raise RunnerError("invalid preflight state intent identity")
    stage_identity = payload["stage_stable_identity"]
    if (
        type(stage_identity) is not list
        or not stage_identity
        or any(type(item) is not int or item < 0 for item in stage_identity)
        or type(payload["stage_size_bytes"]) is not int
        or payload["stage_size_bytes"] < 0
    ):
        raise RunnerError("invalid preflight state stage identity")
    _validate_digest(payload["stage_sha256"], "preflight state stage")
    if payload["admission"] == "absent":
        if any(
            payload[field] is not None
            for field in (
                "initial_stable_identity",
                "initial_sha256",
                "initial_size_bytes",
            )
        ):
            raise RunnerError("absent state intent carries an initial identity")
    else:
        initial_identity = payload["initial_stable_identity"]
        if (
            type(initial_identity) is not list
            or not initial_identity
            or any(type(item) is not int or item < 0 for item in initial_identity)
            or type(payload["initial_size_bytes"]) is not int
            or payload["initial_size_bytes"] < 0
        ):
            raise RunnerError("initialized state intent identity is invalid")
        _validate_digest(payload["initial_sha256"], "preflight initial state")
    return dict(payload)


def _state_from_held_file(
    authority: _HeldRegularFileAuthority,
) -> tuple[dict[str, Any], bytes]:
    content = _read_held_regular_file_bytes(authority)
    if _sha256_bytes(content) != authority.sha256 or len(content) != authority.size_bytes:
        raise RunnerError("held Phase B state bytes changed")
    state = _validate_state(_load_json_object_bytes(content, "Phase B state"))
    if canonical_json_bytes(state) != content:
        raise RunnerError("Phase B state bytes are not canonical")
    return state, content


def _state_intent_matches_file(
    intent: Mapping[str, Any],
    authority: _HeldRegularFileAuthority,
    *,
    prefix: str,
) -> bool:
    return (
        list(authority.stable_identity) == intent[f"{prefix}_stable_identity"]
        and authority.sha256 == intent[f"{prefix}_sha256"]
        and authority.size_bytes == intent[f"{prefix}_size_bytes"]
    )


_NON_LOCKBOX_STATE_INTENT_FIELDS = frozenset(
    {
        "schema_version",
        "operation",
        "source_phase",
        "target_phase",
        "destination_name",
        "stage_name",
        "prior_name",
        "initial_stable_identity",
        "initial_sha256",
        "initial_size_bytes",
        "stage_stable_identity",
        "stage_sha256",
        "stage_size_bytes",
    }
)


def _validate_non_lockbox_state_transition(
    initial_state: Mapping[str, Any],
    target_state: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    initial = _validate_state(dict(initial_state))
    target = _validate_state(dict(target_state))
    if initial["phase"] != "preflight_complete":
        raise RunnerError("non-lockbox state source must be preflight_complete")
    expected = dict(initial)
    expected.update(
        {
            "phase": "non_lockbox_complete",
            "non_lockbox_packet_sha256": target["non_lockbox_packet_sha256"],
        }
    )
    if target != expected:
        raise RunnerError("non-lockbox state transition changed forbidden fields")
    return initial, target


def _non_lockbox_state_intent_payload(
    paths: RunnerPaths,
    *,
    stage: _HeldRegularFileAuthority,
    admitted: _AdmittedNonLockboxStateAuthority,
) -> dict[str, Any]:
    _validate_digest(stage.sha256, "non-lockbox state stage")
    return {
        "schema_version": _REPLACE_INTENT_SCHEMA_VERSION,
        "operation": "non_lockbox",
        "source_phase": "preflight_complete",
        "target_phase": "non_lockbox_complete",
        "destination_name": paths.state_path.name,
        "stage_name": paths.non_lockbox_state_stage_path.name,
        "prior_name": paths.non_lockbox_state_prior_path.name,
        "initial_stable_identity": list(admitted.initial_file.stable_identity),
        "initial_sha256": admitted.initial_file.sha256,
        "initial_size_bytes": admitted.initial_file.size_bytes,
        "stage_stable_identity": list(stage.stable_identity),
        "stage_sha256": stage.sha256,
        "stage_size_bytes": stage.size_bytes,
    }


def _validate_non_lockbox_state_intent(
    payload: Any,
    paths: RunnerPaths,
) -> dict[str, Any]:
    if (
        type(payload) is not dict
        or any(type(key) is not str for key in payload)
        or set(payload) != _NON_LOCKBOX_STATE_INTENT_FIELDS
    ):
        raise RunnerError("invalid non-lockbox state intent fields")
    exact_string_fields = (
        "operation",
        "source_phase",
        "target_phase",
        "destination_name",
        "stage_name",
        "prior_name",
        "initial_sha256",
        "stage_sha256",
    )
    if (
        type(payload["schema_version"]) is not int
        or payload["schema_version"] != _REPLACE_INTENT_SCHEMA_VERSION
        or any(type(payload[field]) is not str for field in exact_string_fields)
        or payload["operation"] != "non_lockbox"
        or payload["source_phase"] != "preflight_complete"
        or payload["target_phase"] != "non_lockbox_complete"
        or payload["destination_name"] != paths.state_path.name
        or payload["stage_name"] != paths.non_lockbox_state_stage_path.name
        or payload["prior_name"] != paths.non_lockbox_state_prior_path.name
    ):
        raise RunnerError("invalid non-lockbox state intent identity")
    for prefix in ("initial", "stage"):
        identity = payload[f"{prefix}_stable_identity"]
        size = payload[f"{prefix}_size_bytes"]
        if (
            type(identity) is not list
            or not identity
            or any(type(item) is not int or item < 0 for item in identity)
            or type(size) is not int
            or size < 0
        ):
            raise RunnerError(
                f"invalid non-lockbox state {prefix} identity"
            )
        _validate_digest(
            payload[f"{prefix}_sha256"],
            f"non-lockbox state {prefix}",
        )
    return dict(payload)


def _recover_non_lockbox_state_controls(
    paths: RunnerPaths,
    *,
    state_root: _HeldDirectoryAuthority,
) -> None:
    state_path = Path(paths.state_path)
    stage_path = Path(paths.non_lockbox_state_stage_path)
    intent_path = Path(paths.non_lockbox_state_intent_path)
    prior_path = Path(paths.non_lockbox_state_prior_path)
    intent_exists = os.path.lexists(intent_path)
    prior_exists = os.path.lexists(prior_path)
    stage_exists = os.path.lexists(stage_path)

    if not intent_exists:
        if prior_exists:
            raise RunnerError(
                "non-lockbox state recovery is indeterminate; orphan prior retained"
            )
        if not stage_exists:
            return
        target_file: _HeldRegularFileAuthority | None = None
        stage_file: _HeldRegularFileAuthority | None = None
        cleanup_started = False
        try:
            if not os.path.lexists(state_path):
                raise RunnerError(
                    "non-lockbox state recovery is indeterminate; orphan stage retained"
                )
            target_file = _open_owned_regular_file_authority(
                state_path,
                parent_authority=state_root,
                delete_access=True,
            )
            stage_file = _open_owned_regular_file_authority(
                stage_path,
                parent_authority=state_root,
                delete_access=True,
            )
            initial_state, _ = _state_from_held_file(target_file)
            target_state, _ = _state_from_held_file(stage_file)
            _validate_non_lockbox_state_transition(initial_state, target_state)
            owned_stage = stage_file
            stage_file = None
            cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
            _flush_held_directory(state_root)
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
            return
        except Exception as error:
            if cleanup_started and not (
                isinstance(error, RunnerError) and "indeterminate" in str(error)
            ):
                raise RunnerError(
                    "non-lockbox state precommit recovery cleanup failed"
                ) from error
            raise
        finally:
            active_error = sys.exc_info()[1]
            remaining = tuple(
                authority
                for authority in (target_file, stage_file)
                if authority is not None
            )
            close_error = _close_owned_regular_file_authorities_once(remaining)
            if close_error is not None:
                _raise_owner_cleanup_failure(
                    "non-lockbox state recovery owner cleanup failed",
                    close_error,
                    active_error=active_error,
                )

    intent_file = _open_owned_regular_file_authority(
        intent_path,
        parent_authority=state_root,
        delete_access=True,
    )
    target_file: _HeldRegularFileAuthority | None = None
    stage_file: _HeldRegularFileAuthority | None = None
    prior_file: _HeldRegularFileAuthority | None = None
    committed_target_recognized = False
    precommit_cleanup_started = False
    try:
        intent_bytes = _read_held_regular_file_bytes(intent_file)
        intent = _validate_non_lockbox_state_intent(
            _load_json_object_bytes(
                intent_bytes,
                "non-lockbox state replacement intent",
            ),
            paths,
        )
        if canonical_json_bytes(intent) != intent_bytes:
            raise RunnerError("non-lockbox state intent is not canonical; retained")
        if os.path.lexists(state_path):
            target_file = _open_owned_regular_file_authority(
                state_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if stage_exists:
            stage_file = _open_owned_regular_file_authority(
                stage_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if prior_exists:
            prior_file = _open_owned_regular_file_authority(
                prior_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if stage_file is not None and not _state_intent_matches_file(
            intent,
            stage_file,
            prefix="stage",
        ):
            raise RunnerError("non-lockbox state stage identity mismatch; retained")
        if prior_file is not None and not _state_intent_matches_file(
            intent,
            prior_file,
            prefix="initial",
        ):
            raise RunnerError("non-lockbox state prior identity mismatch; retained")

        target_state: dict[str, Any] | None = None
        stage_state: dict[str, Any] | None = None
        prior_state: dict[str, Any] | None = None
        if target_file is not None:
            target_state, _ = _state_from_held_file(target_file)
        if stage_file is not None:
            stage_state, _ = _state_from_held_file(stage_file)
        if prior_file is not None:
            prior_state, _ = _state_from_held_file(prior_file)

        if (
            target_file is not None
            and target_state is not None
            and stage_file is None
            and _state_intent_matches_file(intent, target_file, prefix="stage")
        ):
            if target_state["phase"] != intent["target_phase"]:
                raise RunnerError(
                    "non-lockbox committed target phase mismatch; retained"
                )
            if prior_state is not None:
                _validate_non_lockbox_state_transition(prior_state, target_state)
            else:
                try:
                    derived_source = dict(target_state)
                    derived_source.update(
                        {
                            "phase": "preflight_complete",
                            "non_lockbox_packet_sha256": UNSET_DIGEST,
                        }
                    )
                    derived_source = _validate_state(derived_source)
                    _validate_non_lockbox_state_transition(
                        derived_source,
                        target_state,
                    )
                    derived_source_bytes = canonical_json_bytes(derived_source)
                    if (
                        _sha256_bytes(derived_source_bytes)
                        != intent["initial_sha256"]
                        or len(derived_source_bytes)
                        != intent["initial_size_bytes"]
                    ):
                        raise RunnerError(
                            "derived non-lockbox source does not match intent"
                        )
                except Exception as error:
                    raise RunnerError(
                        "non-lockbox state recovery is indeterminate; evidence retained"
                    ) from error
            committed_target_recognized = True
            _flush_held_directory(state_root)
            if prior_file is not None:
                owned_prior = prior_file
                prior_file = None
                _safe_unlink_owned_file(owned_prior)
            owned_intent = intent_file
            intent_file = None
            _safe_unlink_owned_file(owned_intent)
            _flush_held_directory(state_root)
            _verify_held_regular_file_authority(target_file)
            recovered_state, recovered_bytes = _state_from_held_file(target_file)
            if (
                recovered_state != target_state
                or recovered_bytes != canonical_json_bytes(target_state)
                or not _state_intent_matches_file(
                    intent,
                    target_file,
                    prefix="stage",
                )
            ):
                raise RunnerError(
                    "recovered committed non-lockbox state changed after cleanup"
                )
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
            return

        if (
            target_file is not None
            and target_state is not None
            and stage_file is None
            and prior_file is None
            and _state_intent_matches_file(intent, target_file, prefix="initial")
        ):
            if target_state["phase"] != intent["source_phase"]:
                raise RunnerError(
                    "non-lockbox restored target phase mismatch; retained"
                )
            precommit_cleanup_started = True
        elif (
            target_file is not None
            and target_state is not None
            and stage_file is not None
            and stage_state is not None
            and prior_file is None
            and _state_intent_matches_file(intent, target_file, prefix="initial")
        ):
            _validate_non_lockbox_state_transition(target_state, stage_state)
            owned_stage = stage_file
            stage_file = None
            precommit_cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
        elif (
            target_file is None
            and stage_file is not None
            and stage_state is not None
            and prior_file is not None
            and prior_state is not None
        ):
            _validate_non_lockbox_state_transition(prior_state, stage_state)
            try:
                target_file = _renamed_held_regular_file_authority(
                    prior_file,
                    state_path,
                    parent_authority=state_root,
                )
                prior_file = None
            except Exception:
                if os.path.lexists(state_path):
                    status = os.stat(state_path, follow_symlinks=False)
                    if _status_stable_identity(status) == prior_file.stable_identity:
                        target_file = _retargeted_held_regular_file_authority(
                            prior_file,
                            state_path,
                        )
                        prior_file = None
                    else:
                        raise
                else:
                    raise
            owned_stage = stage_file
            stage_file = None
            precommit_cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
        else:
            raise RunnerError(
                "non-lockbox state recovery is indeterminate; evidence retained"
            )
        owned_intent = intent_file
        intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(state_root)
        if target_file is None:
            raise RunnerError("non-lockbox state recovery lost the restored target")
        restored_state, restored_bytes = _state_from_held_file(target_file)
        if (
            restored_state["phase"] != "preflight_complete"
            or not _state_intent_matches_file(intent, target_file, prefix="initial")
            or restored_bytes != canonical_json_bytes(restored_state)
        ):
            raise RunnerError("restored non-lockbox prior changed")
        _validate_state_root_allowlist(
            paths,
            state_root,
            allow_state_controls=False,
        )
    except Exception as error:
        if committed_target_recognized and not (
            isinstance(error, RunnerError) and "indeterminate" in str(error)
        ):
            raise RunnerError(
                "non-lockbox state recovery outcome is indeterminate during "
                "committed cleanup"
            ) from error
        if precommit_cleanup_started and not (
            isinstance(error, RunnerError) and "indeterminate" in str(error)
        ):
            raise RunnerError(
                "non-lockbox state precommit recovery cleanup failed"
            ) from error
        raise
    finally:
        active_error = sys.exc_info()[1]
        remaining = tuple(
            authority
            for authority in (target_file, stage_file, prior_file, intent_file)
            if authority is not None
        )
        close_error = _close_owned_regular_file_authorities_once(remaining)
        if close_error is not None:
            message = "non-lockbox state recovery owner cleanup failed"
            if active_error is not None and "indeterminate" in str(active_error):
                message = (
                    "non-lockbox state recovery remains indeterminate during "
                    "owner cleanup"
                )
            _raise_owner_cleanup_failure(
                message,
                close_error,
                active_error=active_error,
            )


def _recover_preflight_state_controls(
    paths: RunnerPaths,
    *,
    state_root: _HeldDirectoryAuthority,
) -> _HeldRegularFileAuthority | None:
    state_path = Path(paths.state_path)
    stage_path = Path(paths.preflight_state_stage_path)
    intent_path, prior_path = _state_replacement_paths(paths)
    intent_exists = os.path.lexists(intent_path)
    prior_exists = os.path.lexists(prior_path)
    stage_exists = os.path.lexists(stage_path)

    if not intent_exists:
        if prior_exists:
            raise RunnerError(
                "preflight state recovery is indeterminate; orphan prior retained"
            )
        state_file = (
            _open_owned_regular_file_authority(
                state_path,
                parent_authority=state_root,
                delete_access=True,
            )
            if os.path.lexists(state_path)
            else None
        )
        stage: _HeldRegularFileAuthority | None = None
        cleanup_started = False
        try:
            target_state: dict[str, Any] | None = None
            target_bytes: bytes | None = None
            if state_file is not None:
                try:
                    target_state, target_bytes = _state_from_held_file(state_file)
                except RunnerError as error:
                    if stage_exists:
                        raise RunnerError(
                            "preflight state target and no-intent stage coexistence "
                            "is indeterminate; evidence retained"
                        ) from error
                    raise
            if stage_exists:
                stage = _open_owned_regular_file_authority(
                    stage_path,
                    parent_authority=state_root,
                    delete_access=True,
                )
                stage_state, _ = _state_from_held_file(stage)
                if stage_state["phase"] != "preflight_complete":
                    raise RunnerError("malformed state stage is retained")
                if state_file is not None and (
                    target_state != _initial_state()
                    or target_bytes != canonical_json_bytes(_initial_state())
                ):
                    raise RunnerError(
                        "preflight state target and no-intent stage coexistence "
                        "is indeterminate; evidence retained"
                    )
                owned_stage = stage
                stage = None
                cleanup_started = True
                _safe_unlink_owned_file(owned_stage)
                _flush_held_directory(state_root)
            result = state_file
            state_file = None
            return result
        except Exception as error:
            if cleanup_started and not (
                isinstance(error, RunnerError) and "indeterminate" in str(error)
            ):
                raise RunnerError(
                    "preflight state precommit recovery cleanup failed"
                ) from error
            raise
        finally:
            active_error = sys.exc_info()[1]
            remaining = tuple(
                authority
                for authority in (state_file, stage)
                if authority is not None
            )
            state_file = None
            stage = None
            close_error = _close_owned_regular_file_authorities_once(remaining)
            if close_error is not None:
                message = "preflight state recovery owner cleanup failed"
                if active_error is not None and "indeterminate" in str(active_error):
                    message = (
                        "preflight state recovery remains indeterminate during "
                        "owner cleanup"
                    )
                _raise_owner_cleanup_failure(
                    message,
                    close_error,
                    active_error=active_error,
                )

    intent_file = _open_owned_regular_file_authority(
        intent_path,
        parent_authority=state_root,
        delete_access=True,
    )
    target_file: _HeldRegularFileAuthority | None = None
    stage_file: _HeldRegularFileAuthority | None = None
    prior_file: _HeldRegularFileAuthority | None = None
    committed_target_recognized = False
    precommit_cleanup_started = False
    try:
        intent = _validate_state_replacement_intent(
            _load_json_object_bytes(
                _read_held_regular_file_bytes(intent_file),
                "preflight state replacement intent",
            ),
            paths,
        )
        if os.path.lexists(state_path):
            target_file = _open_owned_regular_file_authority(
                state_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if stage_exists:
            stage_file = _open_owned_regular_file_authority(
                stage_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if prior_exists:
            prior_file = _open_owned_regular_file_authority(
                prior_path,
                parent_authority=state_root,
                delete_access=True,
            )
        if stage_file is not None and not _state_intent_matches_file(
            intent,
            stage_file,
            prefix="stage",
        ):
            raise RunnerError("preflight state stage identity mismatch; retained")
        if prior_file is not None and (
            intent["admission"] != "initialized"
            or not _state_intent_matches_file(intent, prior_file, prefix="initial")
        ):
            raise RunnerError("preflight state prior identity mismatch; retained")

        target_state: dict[str, Any] | None = None
        if target_file is not None:
            target_state, _ = _state_from_held_file(target_file)
        if (
            target_file is not None
            and target_state is not None
            and target_state["phase"] != "initialized"
            and _state_intent_matches_file(intent, target_file, prefix="stage")
            and stage_file is None
        ):
            committed_target_recognized = True
            _flush_held_directory(state_root)
            if prior_file is not None:
                owned_prior = prior_file
                prior_file = None
                _safe_unlink_owned_file(owned_prior)
            owned_intent = intent_file
            intent_file = None
            _safe_unlink_owned_file(owned_intent)
            _flush_held_directory(state_root)
            _verify_held_regular_file_authority(target_file)
            recovered_state, recovered_bytes = _state_from_held_file(target_file)
            if (
                recovered_state != target_state
                or recovered_bytes != canonical_json_bytes(target_state)
                or not _state_intent_matches_file(
                    intent,
                    target_file,
                    prefix="stage",
                )
            ):
                raise RunnerError(
                    "recovered committed preflight state changed after cleanup"
                )
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
            result = target_file
            target_file = None
            return result

        if (
            target_file is None
            and stage_file is not None
            and intent["admission"] == "initialized"
            and prior_file is not None
        ):
            target_file = _renamed_held_regular_file_authority(
                prior_file,
                state_path,
                parent_authority=state_root,
            )
            prior_file = None
            owned_stage = stage_file
            stage_file = None
            precommit_cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
        elif (
            target_file is None
            and stage_file is not None
            and intent["admission"] == "absent"
            and prior_file is None
        ):
            owned_stage = stage_file
            stage_file = None
            precommit_cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
        elif (
            target_file is not None
            and target_state is not None
            and target_state["phase"] == "initialized"
            and intent["admission"] == "initialized"
            and _state_intent_matches_file(intent, target_file, prefix="initial")
            and stage_file is not None
            and prior_file is None
        ):
            owned_stage = stage_file
            stage_file = None
            precommit_cleanup_started = True
            _safe_unlink_owned_file(owned_stage)
        else:
            raise RunnerError(
                "preflight state recovery is indeterminate; evidence retained"
            )
        owned_intent = intent_file
        intent_file = None
        _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(state_root)
        result = target_file
        target_file = None
        return result
    except Exception as error:
        if committed_target_recognized and not (
            isinstance(error, RunnerError) and "indeterminate" in str(error)
        ):
            raise RunnerError(
                "preflight state recovery outcome is indeterminate during "
                "committed cleanup"
            ) from error
        if precommit_cleanup_started and not (
            isinstance(error, RunnerError) and "indeterminate" in str(error)
        ):
            raise RunnerError(
                "preflight state precommit recovery cleanup failed"
            ) from error
        raise
    finally:
        active_error = sys.exc_info()[1]
        remaining = tuple(
            authority
            for authority in (target_file, stage_file, prior_file, intent_file)
            if authority is not None
        )
        target_file = None
        stage_file = None
        prior_file = None
        intent_file = None
        close_error = _close_owned_regular_file_authorities_once(remaining)
        if close_error is not None:
            message = "preflight state recovery owner cleanup failed"
            if active_error is not None and "indeterminate" in str(active_error):
                message = (
                    "preflight state recovery remains indeterminate during owner cleanup"
                )
            _raise_owner_cleanup_failure(
                message,
                close_error,
                active_error=active_error,
            )


@contextmanager
def _admit_recovered_state(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
) -> Iterator[_AdmittedStateAuthority | _HeldCommittedStateAuthority]:
    _verify_material_pipeline_authority(material_authority)
    state_root = material_authority.state_root
    present_controls = _validated_state_root_controls(
        paths,
        state_root,
        allow_state_controls=True,
    )
    _reject_mixed_state_control_families(paths, present_controls)
    _recover_non_lockbox_state_controls(paths, state_root=state_root)
    held = _recover_preflight_state_controls(paths, state_root=state_root)
    owner: _RegularFileAuthorityOwner | None = None
    try:
        _validate_state_root_allowlist(paths, state_root, allow_state_controls=False)
        if held is None:
            admitted = _AdmittedStateAuthority(
                admission="absent",
                state_root_stable_identity=state_root.stable_identity,
                initial_bytes=None,
                initial_file=None,
                _initial_owner=None,
            )
            yield admitted
            return
        state, content = _state_from_held_file(held)
        if state["phase"] == "initialized":
            expected = canonical_json_bytes(_initial_state())
            if content != expected:
                raise RunnerError("initialized state is not byte-identical")
            initial_file = held
            held = None
            owner = _RegularFileAuthorityOwner(initial_file)
            yield _AdmittedStateAuthority(
                admission="initialized",
                state_root_stable_identity=state_root.stable_identity,
                initial_bytes=content,
                initial_file=initial_file,
                _initial_owner=owner,
            )
            return
        committed_file = held
        held = None
        owner = _RegularFileAuthorityOwner(committed_file)
        yield _HeldCommittedStateAuthority(
            state=state,
            canonical_bytes=content,
            file=committed_file,
            _file_owner=owner,
        )
    finally:
        active_error = sys.exc_info()[1]
        owned: _HeldRegularFileAuthority | None = None
        if owner is not None:
            remaining = owner.peek()
            if remaining is not None:
                owned = owner.take()
        if held is not None:
            if owned is not None:
                raise RunnerError(
                    "recovered state has duplicate regular-file ownership"
                )
            owned = held
            held = None
        close_error = _close_owned_regular_file_authorities_once(
            (owned,) if owned is not None else ()
        )
        if close_error is not None:
            message = "recovered preflight state owner cleanup failed"
            if active_error is not None and "indeterminate" in str(active_error):
                message = (
                    "preflight state outcome remains indeterminate during recovered "
                    "owner cleanup"
                )
            _raise_owner_cleanup_failure(
                message,
                close_error,
                active_error=active_error,
            )


def _verify_admitted_state_cas(
    paths: RunnerPaths,
    admitted: _AdmittedStateAuthority,
    *,
    state_root: _HeldDirectoryAuthority,
) -> None:
    if (
        type(admitted) is not _AdmittedStateAuthority
        or admitted.state_root_stable_identity != state_root.stable_identity
    ):
        raise RunnerError("admitted state authority changed")
    _verify_held_directory_authority(state_root)
    if admitted.admission == "absent":
        if (
            admitted.initial_file is not None
            or admitted.initial_bytes is not None
            or admitted._initial_owner is not None
        ):
            raise RunnerError("absent state admission carries an initial file")
        if os.path.lexists(paths.state_path):
            raise RunnerError("admitted-absent state target appeared")
        return
    if (
        admitted.admission != "initialized"
        or admitted.initial_file is None
        or admitted._initial_owner is None
        or admitted._initial_owner.peek() is not admitted.initial_file
    ):
        raise RunnerError("initialized state admission is incomplete")
    _verify_held_regular_file_authority(admitted.initial_file)
    content = _read_held_regular_file_bytes(admitted.initial_file)
    if content != admitted.initial_bytes or content != canonical_json_bytes(_initial_state()):
        raise RunnerError("admitted initialized state changed")


@contextmanager
def _commit_preflight_state_durably(
    paths: RunnerPaths,
    state: Mapping[str, Any],
    *,
    material_authority: _MaterialPipelineAuthority,
    admitted_state_authority: _AdmittedStateAuthority,
) -> Iterator[_HeldCommittedStateAuthority]:
    validated_state = _validate_state(dict(state))
    if validated_state["phase"] != "preflight_complete":
        raise RunnerError("preflight state commit requires preflight_complete")
    content = canonical_json_bytes(validated_state)
    _verify_material_pipeline_authority(material_authority)
    state_root = material_authority.state_root
    _verify_admitted_state_cas(
        paths,
        admitted_state_authority,
        state_root=state_root,
    )
    _validate_state_root_allowlist(paths, state_root, allow_state_controls=False)
    stage = _create_held_regular_file_authority(
        paths.preflight_state_stage_path,
        content,
        parent_authority=state_root,
    )
    promoted: _HeldRegularFileAuthority | None = stage
    intent: _HeldRegularFileAuthority | None = None
    prior: _HeldRegularFileAuthority | None = None
    transferred_initial: _HeldRegularFileAuthority | None = None
    committed_owner: _RegularFileAuthorityOwner | None = None
    linearized = False
    try:
        intent_path, prior_path = _state_replacement_paths(paths)
        intent = _create_held_regular_file_authority(
            intent_path,
            canonical_json_bytes(
                _state_replacement_intent_payload(
                    paths,
                    stage=stage,
                    admitted=admitted_state_authority,
                )
            ),
            parent_authority=state_root,
        )
        _verify_admitted_state_cas(
            paths,
            admitted_state_authority,
            state_root=state_root,
        )
        present_controls = _validated_state_root_controls(
            paths,
            state_root,
            allow_state_controls=True,
        )
        _validate_exact_state_control_family(
            paths,
            present_controls,
            family="preflight",
            include_prior=False,
        )
        if admitted_state_authority.admission == "initialized":
            assert admitted_state_authority._initial_owner is not None
            transferred_initial = admitted_state_authority._initial_owner.take()
            if transferred_initial is not admitted_state_authority.initial_file:
                raise RunnerError("initialized state owner transfer changed")
            prior = _renamed_held_regular_file_authority(
                transferred_initial,
                prior_path,
                parent_authority=state_root,
            )
            transferred_initial = prior
            _flush_held_directory(state_root)
        elif os.path.lexists(paths.state_path):
            raise RunnerError("admitted-absent state target appeared before commit")

        present_controls = _validated_state_root_controls(
            paths,
            state_root,
            allow_state_controls=True,
        )
        _validate_exact_state_control_family(
            paths,
            present_controls,
            family="preflight",
            include_prior=(admitted_state_authority.admission == "initialized"),
        )

        promoted = _renamed_held_regular_file_authority(
            stage,
            paths.state_path,
            parent_authority=state_root,
        )
        linearized = True
        _flush_held_directory(state_root)
        _verify_held_regular_file_authority(promoted)
        committed_state, committed_bytes = _state_from_held_file(promoted)
        if committed_bytes != content or committed_state != validated_state:
            raise RunnerError("committed preflight state readback mismatch")
        if prior is not None:
            owned_prior = prior
            prior = None
            transferred_initial = None
            _safe_unlink_owned_file(owned_prior)
        if intent is not None:
            owned_intent = intent
            intent = None
            _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(state_root)
        _validate_state_root_allowlist(paths, state_root, allow_state_controls=False)
        _verify_held_regular_file_authority(promoted)
        post_cleanup_state, post_cleanup_bytes = _state_from_held_file(promoted)
        if (
            post_cleanup_state != committed_state
            or post_cleanup_bytes != committed_bytes
        ):
            raise RunnerError("committed preflight state changed after control cleanup")
        committed_file = promoted
        promoted = None
        committed_owner = _RegularFileAuthorityOwner(committed_file)
        committed = _HeldCommittedStateAuthority(
            state=post_cleanup_state,
            canonical_bytes=post_cleanup_bytes,
            file=committed_file,
            _file_owner=committed_owner,
        )
        try:
            yield committed
            remaining_committed = committed_owner.peek()
            if remaining_committed is not None:
                if remaining_committed is not committed.file:
                    raise RunnerError("committed preflight state owner changed")
                _verify_held_regular_file_authority(remaining_committed)
                final_state, final_bytes = _state_from_held_file(
                    remaining_committed
                )
                if final_state != committed_state or final_bytes != committed_bytes:
                    raise RunnerError("committed preflight state changed")
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
        except Exception as error:
            raise RunnerError(
                f"preflight state outcome is indeterminate: {error}"
            ) from error
    except Exception as error:
        if not linearized:
            try:
                _verify_material_pipeline_authority(material_authority)
                _validate_state_root_allowlist(
                    paths,
                    state_root,
                    allow_state_controls=True,
                )
                entries = _held_non_lockbox_state_root_entry_statuses(
                    paths,
                    state_root,
                    allow_state_controls=True,
                )
                target_status = entries.get(paths.state_path.name)
                stage_status = entries.get(paths.preflight_state_stage_path.name)
                prior_status = entries.get(prior_path.name)
                if target_status is not None:
                    if (
                        promoted is not None
                        and _status_stable_identity(target_status)
                        == promoted.stable_identity
                    ):
                        promoted = _retargeted_held_regular_file_authority(
                            promoted,
                            paths.state_path,
                        )
                        recovered_state, recovered_bytes = _state_from_held_file(
                            promoted
                        )
                        if (
                            recovered_state != validated_state
                            or recovered_bytes != content
                        ):
                            raise RunnerError(
                                "visible renamed state does not match proposed bytes"
                            )
                        linearized = True
                    elif (
                        transferred_initial is not None
                        and _status_stable_identity(target_status)
                        == transferred_initial.stable_identity
                        and admitted_state_authority._initial_owner is not None
                    ):
                        _retargeted_held_regular_file_authority(
                            transferred_initial,
                            paths.state_path,
                        )
                        _verify_held_regular_file_authority(
                            admitted_state_authority.initial_file
                        )
                        admitted_state_authority._initial_owner.restore(
                            admitted_state_authority.initial_file
                        )
                        transferred_initial = None
                        prior = None
                    else:
                        raise RunnerError(
                            "unrecognized state target appeared during rename"
                        )
                elif transferred_initial is not None:
                    if (
                        prior_status is None
                        or _status_stable_identity(prior_status)
                        != transferred_initial.stable_identity
                    ):
                        raise RunnerError(
                            "transferred initialized state is not the held prior"
                        )
                    prior = _retargeted_held_regular_file_authority(
                        transferred_initial,
                        prior_path,
                    )
                    transferred_initial = prior
                if not linearized and promoted is not None:
                    if (
                        stage_status is None
                        or _status_stable_identity(stage_status)
                        != promoted.stable_identity
                    ):
                        raise RunnerError(
                            "held state stage left its reserved precommit entry"
                        )
            except Exception as reconciliation_error:
                raise RunnerError(
                    "preflight state outcome is indeterminate during rename reconciliation"
                ) from reconciliation_error
        if linearized:
            if isinstance(error, RunnerError) and "indeterminate" in str(error):
                raise
            raise RunnerError(
                f"preflight state outcome is indeterminate: {error}"
            ) from error
        try:
            if prior is not None and not os.path.lexists(paths.state_path):
                prior = _renamed_held_regular_file_authority(
                    prior,
                    paths.state_path,
                    parent_authority=state_root,
                )
                transferred_initial = prior
            if (
                admitted_state_authority._initial_owner is not None
                and transferred_initial is not None
            ):
                admitted_state_authority._initial_owner.restore(
                    transferred_initial
                )
                transferred_initial = None
                prior = None
            if promoted is not None and os.path.lexists(promoted.path):
                owned_promoted = promoted
                promoted = None
                _safe_unlink_owned_file(owned_promoted)
            if intent is not None:
                owned_intent = intent
                intent = None
                _safe_unlink_owned_file(owned_intent)
            _flush_held_directory(state_root)
        except Exception as recovery_error:
            raise RunnerError(
                "preflight state outcome is indeterminate during precommit recovery"
            ) from recovery_error
        raise
    finally:
        active_error = sys.exc_info()[1]
        remaining_owners: list[_HeldRegularFileAuthority] = []
        if prior is not None:
            remaining_owners.append(prior)
        elif transferred_initial is not None:
            remaining_owners.append(transferred_initial)
        if intent is not None:
            remaining_owners.append(intent)
        if promoted is not None:
            remaining_owners.append(promoted)
        if committed_owner is not None:
            remaining_committed = committed_owner.peek()
            if remaining_committed is not None:
                remaining_owners.append(committed_owner.take())
        prior = None
        transferred_initial = None
        intent = None
        promoted = None
        close_error = _close_owned_regular_file_authorities_once(remaining_owners)
        if close_error is not None:
            if linearized:
                message = (
                    "preflight state outcome is indeterminate during committed "
                    "owner cleanup"
                )
            elif active_error is not None and "indeterminate" in str(active_error):
                message = (
                    "preflight state outcome is indeterminate during precommit "
                    "owner cleanup"
                )
            else:
                message = (
                    "preflight state precommit owner cleanup failed after "
                    "deterministic recovery"
                )
            _raise_owner_cleanup_failure(
                message,
                close_error,
                active_error=active_error,
            )


def _verify_admitted_non_lockbox_state_cas(
    paths: RunnerPaths,
    admitted: _AdmittedNonLockboxStateAuthority,
    *,
    state_root: _HeldDirectoryAuthority,
) -> None:
    if (
        type(admitted) is not _AdmittedNonLockboxStateAuthority
        or type(admitted._initial_owner) is not _RegularFileAuthorityOwner
        or admitted._initial_owner.peek() is not admitted.initial_file
        or admitted.initial_file.path != Path(paths.state_path)
    ):
        raise RunnerError("admitted non-lockbox state authority changed")
    _verify_held_directory_authority(state_root)
    _verify_held_regular_file_authority(admitted.initial_file)
    state, content = _state_from_held_file(admitted.initial_file)
    if (
        state != admitted.initial_state
        or content != admitted.initial_bytes
        or content != canonical_json_bytes(state)
        or state["phase"] != "preflight_complete"
    ):
        raise RunnerError("admitted preflight state changed before non-lockbox commit")


@contextmanager
def _admit_non_lockbox_state(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
    committed_state_authority: _HeldCommittedStateAuthority,
) -> Iterator[_AdmittedNonLockboxStateAuthority]:
    if type(committed_state_authority) is not _HeldCommittedStateAuthority:
        raise RunnerError("committed preflight state authority type changed")
    _verify_material_pipeline_authority(material_authority)
    state_root = material_authority.state_root
    owner = committed_state_authority._file_owner
    if (
        type(owner) is not _RegularFileAuthorityOwner
        or owner.peek() is not committed_state_authority.file
    ):
        raise RunnerError("committed preflight state owner is unavailable")
    _verify_held_regular_file_authority(committed_state_authority.file)
    initial_state, initial_bytes = _state_from_held_file(
        committed_state_authority.file
    )
    if (
        initial_state != committed_state_authority.state
        or initial_bytes != committed_state_authority.canonical_bytes
        or initial_state["phase"] != "preflight_complete"
    ):
        raise RunnerError(
            "non-lockbox state admission requires exact preflight_complete state"
        )
    _validate_state_root_allowlist(
        paths,
        state_root,
        allow_state_controls=False,
    )
    admitted = _AdmittedNonLockboxStateAuthority(
        initial_state=initial_state,
        initial_bytes=initial_bytes,
        initial_file=committed_state_authority.file,
        _initial_owner=owner,
    )
    try:
        yield admitted
    finally:
        remaining = owner.peek()
        if remaining is not None:
            if remaining is not committed_state_authority.file:
                raise RunnerError("committed preflight state owner changed during admission")
            _verify_admitted_non_lockbox_state_cas(
                paths,
                admitted,
                state_root=state_root,
            )


@contextmanager
def _commit_non_lockbox_state_durably(
    paths: RunnerPaths,
    state: Mapping[str, Any],
    *,
    material_authority: _MaterialPipelineAuthority,
    admitted_state_authority: _AdmittedNonLockboxStateAuthority,
) -> Iterator[_HeldCommittedStateAuthority]:
    validated_state = _validate_state(dict(state))
    initial_state, validated_state = _validate_non_lockbox_state_transition(
        admitted_state_authority.initial_state,
        validated_state,
    )
    content = canonical_json_bytes(validated_state)
    _verify_material_pipeline_authority(material_authority)
    state_root = material_authority.state_root
    _verify_admitted_non_lockbox_state_cas(
        paths,
        admitted_state_authority,
        state_root=state_root,
    )
    _validate_state_root_allowlist(paths, state_root, allow_state_controls=False)
    stage = _create_held_regular_file_authority(
        paths.non_lockbox_state_stage_path,
        content,
        parent_authority=state_root,
    )
    promoted: _HeldRegularFileAuthority | None = stage
    intent: _HeldRegularFileAuthority | None = None
    prior: _HeldRegularFileAuthority | None = None
    transferred_initial: _HeldRegularFileAuthority | None = None
    committed_owner: _RegularFileAuthorityOwner | None = None
    linearized = False
    try:
        intent = _create_held_regular_file_authority(
            paths.non_lockbox_state_intent_path,
            canonical_json_bytes(
                _non_lockbox_state_intent_payload(
                    paths,
                    stage=stage,
                    admitted=admitted_state_authority,
                )
            ),
            parent_authority=state_root,
        )
        _verify_admitted_non_lockbox_state_cas(
            paths,
            admitted_state_authority,
            state_root=state_root,
        )
        present_controls = _validated_state_root_controls(
            paths,
            state_root,
            allow_state_controls=True,
        )
        _validate_exact_state_control_family(
            paths,
            present_controls,
            family="non_lockbox",
            include_prior=False,
        )
        transferred_initial = admitted_state_authority._initial_owner.take()
        if transferred_initial is not admitted_state_authority.initial_file:
            raise RunnerError("non-lockbox initial state owner transfer changed")
        prior = _renamed_held_regular_file_authority(
            transferred_initial,
            paths.non_lockbox_state_prior_path,
            parent_authority=state_root,
        )
        transferred_initial = prior
        _flush_held_directory(state_root)

        present_controls = _validated_state_root_controls(
            paths,
            state_root,
            allow_state_controls=True,
        )
        _validate_exact_state_control_family(
            paths,
            present_controls,
            family="non_lockbox",
            include_prior=True,
        )

        promoted = _renamed_held_regular_file_authority(
            stage,
            paths.state_path,
            parent_authority=state_root,
        )
        linearized = True
        _flush_held_directory(state_root)
        _verify_held_regular_file_authority(promoted)
        committed_state, committed_bytes = _state_from_held_file(promoted)
        if committed_state != validated_state or committed_bytes != content:
            raise RunnerError("committed non-lockbox state readback mismatch")
        if prior is not None:
            owned_prior = prior
            prior = None
            transferred_initial = None
            _safe_unlink_owned_file(owned_prior)
        if intent is not None:
            owned_intent = intent
            intent = None
            _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(state_root)
        _validate_state_root_allowlist(
            paths,
            state_root,
            allow_state_controls=False,
        )
        _verify_held_regular_file_authority(promoted)
        post_cleanup_state, post_cleanup_bytes = _state_from_held_file(promoted)
        if (
            post_cleanup_state != committed_state
            or post_cleanup_bytes != committed_bytes
        ):
            raise RunnerError(
                "committed non-lockbox state changed after control cleanup"
            )
        committed_file = promoted
        promoted = None
        committed_owner = _RegularFileAuthorityOwner(committed_file)
        committed = _HeldCommittedStateAuthority(
            state=post_cleanup_state,
            canonical_bytes=post_cleanup_bytes,
            file=committed_file,
            _file_owner=committed_owner,
        )
        try:
            yield committed
            remaining_committed = committed_owner.peek()
            if remaining_committed is not None:
                if remaining_committed is not committed.file:
                    raise RunnerError("committed non-lockbox state owner changed")
                _verify_held_regular_file_authority(remaining_committed)
                final_state, final_bytes = _state_from_held_file(
                    remaining_committed
                )
                if final_state != committed_state or final_bytes != committed_bytes:
                    raise RunnerError("committed non-lockbox state changed")
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
        except Exception as error:
            raise RunnerError(
                f"non-lockbox state postcommit outcome is indeterminate: {error}"
            ) from error
    except Exception as error:
        if not linearized:
            try:
                _verify_material_pipeline_authority(material_authority)
                _validate_state_root_allowlist(
                    paths,
                    state_root,
                    allow_state_controls=True,
                )
                entries = _held_non_lockbox_state_root_entry_statuses(
                    paths,
                    state_root,
                    allow_state_controls=True,
                )
                target_status = entries.get(paths.state_path.name)
                stage_status = entries.get(paths.non_lockbox_state_stage_path.name)
                prior_status = entries.get(paths.non_lockbox_state_prior_path.name)
                if target_status is not None:
                    if (
                        promoted is not None
                        and _status_stable_identity(target_status)
                        == promoted.stable_identity
                    ):
                        promoted = _retargeted_held_regular_file_authority(
                            promoted,
                            paths.state_path,
                        )
                        recovered_state, recovered_bytes = _state_from_held_file(
                            promoted
                        )
                        if (
                            recovered_state != validated_state
                            or recovered_bytes != content
                        ):
                            raise RunnerError(
                                "visible non-lockbox target does not match stage bytes"
                            )
                        linearized = True
                    elif (
                        transferred_initial is not None
                        and _status_stable_identity(target_status)
                        == transferred_initial.stable_identity
                    ):
                        _retargeted_held_regular_file_authority(
                            transferred_initial,
                            paths.state_path,
                        )
                        _verify_held_regular_file_authority(
                            admitted_state_authority.initial_file
                        )
                        admitted_state_authority._initial_owner.restore(
                            admitted_state_authority.initial_file
                        )
                        transferred_initial = None
                        prior = None
                    elif (
                        admitted_state_authority._initial_owner.peek()
                        is not admitted_state_authority.initial_file
                        or _status_stable_identity(target_status)
                        != admitted_state_authority.initial_file.stable_identity
                    ):
                        raise RunnerError(
                            "unrecognized state target appeared during non-lockbox rename"
                        )
                elif transferred_initial is not None:
                    if (
                        prior_status is None
                        or _status_stable_identity(prior_status)
                        != transferred_initial.stable_identity
                    ):
                        raise RunnerError(
                            "transferred preflight state is not the held prior"
                        )
                    prior = _retargeted_held_regular_file_authority(
                        transferred_initial,
                        paths.non_lockbox_state_prior_path,
                    )
                    transferred_initial = prior
                else:
                    raise RunnerError(
                        "preflight state target disappeared before non-lockbox commit"
                    )
                if not linearized and promoted is not None:
                    if (
                        stage_status is None
                        or _status_stable_identity(stage_status)
                        != promoted.stable_identity
                    ):
                        raise RunnerError(
                            "held non-lockbox state stage left its precommit entry"
                        )
            except Exception as reconciliation_error:
                raise RunnerError(
                    "non-lockbox state outcome is indeterminate during rename "
                    "reconciliation"
                ) from reconciliation_error
        if linearized:
            if isinstance(error, RunnerError) and "indeterminate" in str(error):
                raise
            raise RunnerError(
                f"non-lockbox state postcommit outcome is indeterminate: {error}"
            ) from error
        try:
            if prior is not None and not os.path.lexists(paths.state_path):
                try:
                    restored = _renamed_held_regular_file_authority(
                        prior,
                        paths.state_path,
                        parent_authority=state_root,
                    )
                except Exception:
                    if os.path.lexists(paths.state_path):
                        restored_status = os.stat(
                            paths.state_path,
                            follow_symlinks=False,
                        )
                        if (
                            _status_stable_identity(restored_status)
                            == prior.stable_identity
                        ):
                            restored = _retargeted_held_regular_file_authority(
                                prior,
                                paths.state_path,
                            )
                        else:
                            raise
                    else:
                        raise
                prior = None
                del restored
                _verify_held_regular_file_authority(
                    admitted_state_authority.initial_file
                )
                transferred_initial = admitted_state_authority.initial_file
            if transferred_initial is not None:
                admitted_state_authority._initial_owner.restore(
                    transferred_initial
                )
                transferred_initial = None
                prior = None
            if promoted is not None and os.path.lexists(promoted.path):
                owned_promoted = promoted
                promoted = None
                _safe_unlink_owned_file(owned_promoted)
            if intent is not None:
                owned_intent = intent
                intent = None
                _safe_unlink_owned_file(owned_intent)
            _flush_held_directory(state_root)
            _validate_state_root_allowlist(
                paths,
                state_root,
                allow_state_controls=False,
            )
            _verify_admitted_non_lockbox_state_cas(
                paths,
                admitted_state_authority,
                state_root=state_root,
            )
            restored_state, restored_bytes = _state_from_held_file(
                admitted_state_authority.initial_file
            )
            if restored_state != initial_state or restored_bytes != admitted_state_authority.initial_bytes:
                raise RunnerError("restored preflight state bytes changed")
        except Exception as recovery_error:
            raise RunnerError(
                "non-lockbox state outcome is indeterminate during precommit recovery"
            ) from recovery_error
        if isinstance(error, RunnerError):
            raise
        raise RunnerError(f"non-lockbox state precommit failed: {error}") from error
    finally:
        active_error = sys.exc_info()[1]
        remaining_owners: list[_HeldRegularFileAuthority] = []
        if prior is not None:
            remaining_owners.append(prior)
        elif transferred_initial is not None:
            remaining_owners.append(transferred_initial)
        if intent is not None:
            remaining_owners.append(intent)
        if promoted is not None:
            remaining_owners.append(promoted)
        if committed_owner is not None:
            remaining_committed = committed_owner.peek()
            if remaining_committed is not None:
                remaining_owners.append(committed_owner.take())
        prior = None
        transferred_initial = None
        intent = None
        promoted = None
        close_error = _close_owned_regular_file_authorities_once(remaining_owners)
        if close_error is not None:
            if linearized:
                message = (
                    "non-lockbox state postcommit outcome is indeterminate during "
                    "owner cleanup"
                )
            elif active_error is not None and "indeterminate" in str(active_error):
                message = (
                    "non-lockbox state outcome is indeterminate during precommit "
                    "owner cleanup"
                )
            else:
                message = (
                    "non-lockbox state precommit owner cleanup failed after "
                    "deterministic recovery"
                )
            _raise_owner_cleanup_failure(
                message,
                close_error,
                active_error=active_error,
            )


def _preflight_payload_bytes(
    paths: RunnerPaths,
    artifacts: ProductionPreflightArtifacts,
) -> tuple[tuple[Path, bytes], ...]:
    if type(artifacts) is not ProductionPreflightArtifacts:
        raise RunnerError("exact ProductionPreflightArtifacts value is required")
    _validate_digest(
        artifacts.source_authority_commitment_sha256,
        "source authority commitment",
    )
    try:
        ledger = validate_phase_b_input_ledger(deepcopy(artifacts.input_ledger))
        manifest = validate_phase_b_split_manifest(deepcopy(artifacts.split_manifest))
        if type(artifacts.partition_authority_caches) is not dict or tuple(
            artifacts.partition_authority_caches
        ) != NONFINAL_PARTITION_ROLES:
            raise ValueError("preflight cache roles changed")
        caches = {
            role: validate_phase_b_partition_authority_cache(
                deepcopy(artifacts.partition_authority_caches[role]),
                manifest,
                expected_role=role,
            )
            for role in NONFINAL_PARTITION_ROLES
        }
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid preflight artifacts: {error}") from error
    payloads = (ledger, manifest, *(caches[role] for role in NONFINAL_PARTITION_ROLES))
    return tuple(
        (path, canonical_json_bytes(payload))
        for path, payload in zip(
            _preflight_artifact_destinations(paths),
            payloads,
            strict=True,
        )
    )


def _validate_and_restore_readback_files(
    paths: RunnerPaths,
    files: tuple[_HeldRegularFileAuthority, ...],
) -> tuple[dict[str, Any], dict[str, Any], tuple[Any, ...]]:
    if len(files) != 5:
        raise RunnerError("preflight readback file count changed")
    expected_paths = _preflight_artifact_destinations(paths)
    if tuple(item.path for item in files) != expected_paths:
        raise RunnerError("preflight readback path order changed")
    for authority in files:
        _verify_held_regular_file_authority(authority)
    ledger_bytes, manifest_bytes, *cache_bytes = tuple(
        _read_held_regular_file_bytes(authority) for authority in files
    )
    try:
        ledger = validate_phase_b_input_ledger(
            _load_json_object_bytes(ledger_bytes, "preflight input ledger")
        )
        manifest = validate_phase_b_split_manifest(
            _load_json_object_bytes(manifest_bytes, "preflight split manifest")
        )
        if canonical_json_bytes(ledger) != ledger_bytes:
            raise ValueError("preflight input ledger bytes are not canonical")
        if canonical_json_bytes(manifest) != manifest_bytes:
            raise ValueError("preflight split manifest bytes are not canonical")
        from scripts import emotion_state_phase_b_evaluation as evaluation

        restored: list[Any] = []
        for role, content in zip(
            NONFINAL_PARTITION_ROLES,
            cache_bytes,
            strict=True,
        ):
            cache = validate_phase_b_partition_authority_cache(
                _load_json_object_bytes(content, f"{role} partition cache"),
                manifest,
                expected_role=role,
            )
            if canonical_json_bytes(cache) != content:
                raise ValueError(f"{role} partition cache bytes are not canonical")
            authority = evaluation.restore_validated_partition_authority_cache(
                cache,
                manifest,
                role=role,
            )
            records = evaluation.validated_partition_records(authority, role=role)
            if not records or any(
                hasattr(record, "project_relative_path")
                or hasattr(record.label_record, "project_relative_path")
                for record in records
            ):
                raise ValueError("restored partition records are empty or path-bearing")
            payload = authority.to_payload()
            if (
                payload["partition_role"] != role
                or payload["configuration_sha256"]
                != manifest["configuration_sha256"]
                or payload["split_manifest_sha256"]
                != manifest["split_manifest_sha256"]
                or payload["assignment_sha256"] != manifest["assignment_sha256"]
                or payload["partition_authority_sha256"]
                != manifest["partition_authority_sha256"][role]
            ):
                raise ValueError("restored partition authority link changed")
            restored.append(authority)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"preflight readback validation failed: {error}") from error
    return ledger, manifest, tuple(restored)


@contextmanager
def _persist_preflight_artifacts(
    paths: RunnerPaths,
    artifacts: ProductionPreflightArtifacts,
    *,
    material_authority: _MaterialPipelineAuthority,
    output_authorities: _PreflightOutputAuthorities,
) -> Iterator[_PersistedPreflightReadback]:
    _verify_material_pipeline_authority(material_authority)
    if type(output_authorities) is not _PreflightOutputAuthorities:
        raise RunnerError("preflight output authority type changed")
    payload_bytes = _preflight_payload_bytes(paths, artifacts)
    for destination, content in payload_bytes:
        _replace_preflight_bytes_durably(
            paths,
            destination,
            content,
            output_authorities=output_authorities,
        )
    _validate_preflight_output_shape(
        paths,
        output_authorities,
        require_complete=True,
        allow_controls=False,
    )
    with ExitStack() as stack:
        files = tuple(
            stack.enter_context(_held_regular_file(destination))
            for destination, _content in payload_bytes
        )
        for authority, (_destination, expected) in zip(
            files,
            payload_bytes,
            strict=True,
        ):
            if _read_held_regular_file_bytes(authority) != expected:
                raise RunnerError("persisted preflight artifact bytes changed")
        ledger, manifest, _restored = _validate_and_restore_readback_files(
            paths,
            files,
        )
        readback = _PersistedPreflightReadback(
            input_ledger=ledger,
            split_manifest=manifest,
            files=files,
        )
        try:
            yield readback
        finally:
            for authority in files:
                _verify_held_regular_file_authority(authority)
            _validate_preflight_output_shape(
                paths,
                output_authorities,
                require_complete=True,
                allow_controls=False,
            )


def _non_lockbox_artifact_destinations(
    paths: RunnerPaths,
) -> tuple[Path, ...]:
    if tuple(NON_LOCKBOX_ROLE_ORDER) != NONFINAL_PARTITION_ROLES:
        raise RunnerError("non-lockbox role order changed")
    destinations = (
        *(Path(paths.non_lockbox_feature_cache_path(role)) for role in NONFINAL_PARTITION_ROLES),
        Path(paths.non_lockbox_ami_evidence_path),
        Path(paths.non_lockbox_packet_path),
    )
    expected_packet = Path(paths.non_lockbox_root) / "non-lockbox-packet.json"
    if destinations[-1] != expected_packet:
        raise RunnerError("non-lockbox packet destination is not fixed")
    return destinations


def _non_lockbox_artifact_stage_path(destination: Path) -> Path:
    target = Path(destination)
    return target.with_name(f".{target.name}.non-lockbox.stage")


def _non_lockbox_output_parent_for_destination(
    paths: RunnerPaths,
    destination: Path,
    authorities: _NonLockboxOutputAuthorities,
) -> _HeldDirectoryAuthority:
    target = Path(destination)
    destinations = _non_lockbox_artifact_destinations(paths)
    if target in destinations[:4]:
        parent = authorities.cache_root
    elif target == destinations[4]:
        parent = authorities.root
    else:
        raise RunnerError("non-lockbox artifact destination is not fixed")
    if target.parent != parent.path:
        raise RunnerError("non-lockbox artifact parent authority changed")
    _verify_held_directory_authority(parent)
    return parent


def _validate_non_lockbox_self_hashed_payload(
    payload: Any,
    *,
    label: str,
    expected_fields: tuple[str, ...],
    role: str | None = None,
) -> dict[str, Any]:
    if (
        type(payload) is not dict
        or any(type(key) is not str for key in payload)
        or tuple(payload) != expected_fields
        or type(payload.get("self_sha256")) is not str
    ):
        raise RunnerError(f"invalid {label} shape")
    if role is not None and (
        type(payload.get("partition_role")) is not str
        or payload["partition_role"] != role
    ):
        raise RunnerError(f"invalid {label} partition role")
    try:
        expected = canonical_payload_sha256(payload)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid {label}: {error}") from error
    if payload["self_sha256"] != expected:
        raise RunnerError(f"invalid {label} self commitment")
    _validate_digest(payload["self_sha256"], f"{label} self")
    return deepcopy(payload)


def _validated_non_lockbox_payload_for_destination(
    paths: RunnerPaths,
    destination: Path,
    payload: Any,
) -> dict[str, Any]:
    target = Path(destination)
    destinations = _non_lockbox_artifact_destinations(paths)
    if target in destinations[:3]:
        role = NONFINAL_PARTITION_ROLES[destinations.index(target)]
        cache = _validate_non_lockbox_self_hashed_payload(
            payload,
            label=f"{role} feature cache",
            expected_fields=NON_LOCKBOX_FEATURE_CACHE_FIELDS,
            role=role,
        )
        feature_names = cache.get("feature_names")
        records = cache.get("records")
        if (
            type(feature_names) is not list
            or not feature_names
            or any(type(name) is not str or not name for name in feature_names)
            or len(set(feature_names)) != len(feature_names)
            or type(records) is not list
            or not records
        ):
            raise RunnerError(f"invalid {role} feature cache record shape")
        for record in records:
            if (
                type(record) is not dict
                or tuple(record) != NON_LOCKBOX_FEATURE_RECORD_FIELDS
                or type(record.get("clip_stem")) is not str
                or not record["clip_stem"]
                or type(record.get("audio_sha256")) is not str
                or type(record.get("audio_size_bytes")) is not int
                or record["audio_size_bytes"] <= 0
                or type(record.get("features")) is not dict
                or tuple(record["features"]) != tuple(feature_names)
                or any(
                    type(value) is not float or not math.isfinite(value)
                    for value in record["features"].values()
                )
            ):
                raise RunnerError(f"invalid {role} feature cache record")
            _validate_digest(
                record["audio_sha256"],
                f"{role} feature-cache audio",
            )
        return cache
    if target == destinations[3]:
        return _validate_non_lockbox_self_hashed_payload(
            payload,
            label="AMI evidence cache",
            expected_fields=NON_LOCKBOX_AMI_EVIDENCE_FIELDS,
        )
    if target == destinations[4]:
        if type(payload) is not dict or any(
            type(key) is not str for key in payload
        ):
            raise RunnerError("invalid non-lockbox packet shape")
        try:
            public = validate_non_lockbox_review_packet(deepcopy(payload))
            independent = validate_non_lockbox_packet(deepcopy(payload))
        except (TypeError, ValueError) as error:
            raise RunnerError(f"invalid non-lockbox packet: {error}") from error
        if (
            type(public) is not dict
            or type(independent) is not dict
            or canonical_json_bytes(public) != canonical_json_bytes(payload)
            or canonical_json_bytes(independent) != canonical_json_bytes(payload)
        ):
            raise RunnerError("non-lockbox packet validators disagree")
        return deepcopy(payload)
    raise RunnerError("non-lockbox artifact destination is not fixed")


def _non_lockbox_payload_bytes(
    paths: RunnerPaths,
    artifacts: ProductionNonLockboxArtifacts,
) -> tuple[tuple[Path, bytes], ...]:
    if type(artifacts) is not ProductionNonLockboxArtifacts:
        raise RunnerError("exact ProductionNonLockboxArtifacts value is required")
    if (
        type(artifacts.feature_caches) is not dict
        or tuple(artifacts.feature_caches) != NONFINAL_PARTITION_ROLES
        or any(
            type(role) is not str or type(payload) is not dict
            for role, payload in artifacts.feature_caches.items()
        )
        or type(artifacts.ami_evidence) is not dict
        or type(artifacts.review_packet) is not dict
    ):
        raise RunnerError("non-lockbox artifact aggregate shape changed")
    destinations = _non_lockbox_artifact_destinations(paths)
    payloads = (
        *(artifacts.feature_caches[role] for role in NONFINAL_PARTITION_ROLES),
        artifacts.ami_evidence,
        artifacts.review_packet,
    )
    validated = tuple(
        _validated_non_lockbox_payload_for_destination(
            paths,
            destination,
            deepcopy(payload),
        )
        for destination, payload in zip(destinations, payloads, strict=True)
    )
    expected_commitments = {
        **{
            role: validated[index]["self_sha256"]
            for index, role in enumerate(NONFINAL_PARTITION_ROLES)
        },
        "ami_evidence": validated[3]["self_sha256"],
    }
    if validated[4].get("artifact_cache_commitments") != expected_commitments:
        raise RunnerError("non-lockbox packet cache commitments changed")
    return tuple(
        (destination, _non_lockbox_artifact_json_bytes(payload))
        for destination, payload in zip(destinations, validated, strict=True)
    )


def _parse_non_lockbox_artifact_bytes(
    paths: RunnerPaths,
    destination: Path,
    content: bytes,
) -> dict[str, Any]:
    if type(content) is not bytes:
        raise RunnerError("non-lockbox artifact readback is not bytes")
    payload = _load_json_object_bytes(
        content,
        f"{Path(destination).name} non-lockbox artifact",
    )
    validated = _validated_non_lockbox_payload_for_destination(
        paths,
        destination,
        payload,
    )
    if _non_lockbox_artifact_json_bytes(validated) != content:
        raise RunnerError("non-lockbox artifact bytes are not canonical")
    return validated


def _validate_non_lockbox_output_shape(
    paths: RunnerPaths,
    authorities: _NonLockboxOutputAuthorities,
    *,
    require_complete: bool,
    allow_controls: bool,
) -> None:
    if type(authorities) is not _NonLockboxOutputAuthorities:
        raise RunnerError("non-lockbox output authority type changed")
    expected_roots = (
        Path(paths.non_lockbox_root),
        Path(paths.non_lockbox_cache_root),
    )
    held_roots = (authorities.root, authorities.cache_root)
    if any(
        type(authority) is not _HeldDirectoryAuthority
        or authority.path != expected
        for authority, expected in zip(held_roots, expected_roots, strict=True)
    ):
        raise RunnerError("non-lockbox output capability does not match paths")
    destinations = _non_lockbox_artifact_destinations(paths)
    groups = (
        (authorities.root, destinations[4:]),
        (authorities.cache_root, destinations[:4]),
    )
    for parent, fixed_destinations in groups:
        fixed_names = {destination.name for destination in fixed_destinations}
        control_names: set[str] = set()
        for destination in fixed_destinations:
            intent, prior = _replacement_control_paths(destination)
            control_names.update({
                _non_lockbox_artifact_stage_path(destination).name,
                intent.name,
                prior.name,
            })
        entries = _held_directory_entry_statuses(parent)
        if parent is authorities.root:
            unknown = set(entries) - fixed_names - control_names - {"cache"}
        else:
            unknown = set(entries) - fixed_names - control_names
        if unknown:
            raise RunnerError(
                "unknown non-lockbox output entry is retained: "
                + ", ".join(sorted(unknown))
            )
        if not allow_controls and set(entries) & control_names:
            raise RunnerError("non-lockbox recovery control is retained")
        expected_names = set(fixed_names)
        if parent is authorities.root:
            expected_names.add("cache")
            cache_status = entries.get("cache")
            if cache_status is None:
                raise RunnerError("non-lockbox cache root is missing")
            _require_safe_directory_entry(parent, "cache", cache_status)
        if require_complete and set(entries) != expected_names:
            raise RunnerError("non-lockbox output shape is incomplete")
        for name, status in entries.items():
            if parent is authorities.root and name == "cache":
                continue
            _require_safe_regular_entry(parent, name, status)


def _non_lockbox_recovery_plan_files(
    plan: _NonLockboxArtifactRecoveryPlan,
) -> tuple[_HeldRegularFileAuthority, ...]:
    return tuple(
        authority
        for authority in (
            plan.destination_file,
            plan.intent_file,
            plan.prior_file,
            plan.stage_file,
        )
        if authority is not None
    )


def _close_non_lockbox_recovery_plan(
    plan: _NonLockboxArtifactRecoveryPlan,
) -> None:
    files = _non_lockbox_recovery_plan_files(plan)
    plan.destination_file = None
    plan.intent_file = None
    plan.prior_file = None
    plan.stage_file = None
    close_error = _close_owned_regular_file_authorities_once(files)
    if close_error is not None:
        raise close_error


def _plan_non_lockbox_artifact_destination_recovery(
    paths: RunnerPaths,
    destination: Path,
    *,
    parent_authority: _HeldDirectoryAuthority,
    entry_names: frozenset[str],
) -> _NonLockboxArtifactRecoveryPlan:
    target = Path(destination)
    if target.parent != parent_authority.path:
        raise RunnerError("non-lockbox recovery parent authority changed")
    stage_path = _non_lockbox_artifact_stage_path(target)
    intent_path, prior_path = _replacement_control_paths(target)
    recognized_names = {
        target.name,
        stage_path.name,
        intent_path.name,
        prior_path.name,
    }
    if not entry_names <= recognized_names:
        raise RunnerError("non-lockbox recovery received an unknown entry")

    opened: list[_HeldRegularFileAuthority] = []

    def open_if_present(path: Path) -> _HeldRegularFileAuthority | None:
        if path.name not in entry_names:
            return None
        authority = _open_owned_regular_file_authority(
            path,
            parent_authority=parent_authority,
            delete_access=True,
        )
        opened.append(authority)
        return authority

    try:
        destination_file = open_if_present(target)
        intent_file = open_if_present(intent_path)
        prior_file = open_if_present(prior_path)
        stage_file = open_if_present(stage_path)
        for label, authority in (
            ("destination", destination_file),
            ("prior", prior_file),
            ("stage", stage_file),
        ):
            if authority is not None:
                try:
                    _parse_non_lockbox_artifact_bytes(
                        paths,
                        target,
                        _read_held_regular_file_bytes(authority),
                    )
                except RunnerError as error:
                    raise RunnerError(
                        f"malformed non-lockbox {label} is retained"
                    ) from error
        if intent_file is None:
            if prior_file is not None:
                raise RunnerError("orphaned non-lockbox prior is retained")
            action = "discard-stage" if stage_file is not None else "none"
        else:
            intent_bytes = _read_held_regular_file_bytes(intent_file)
            try:
                intent = _validate_replacement_intent(
                    _load_json_object_bytes(
                        intent_bytes,
                        "non-lockbox replacement intent",
                    ),
                    destination=target,
                    prior_path=prior_path,
                )
            except RunnerError as error:
                raise RunnerError(
                    "malformed non-lockbox replacement intent is retained"
                ) from error
            if canonical_json_bytes(intent) != intent_bytes:
                raise RunnerError(
                    "noncanonical non-lockbox replacement intent is retained"
                )
            if (
                destination_file is not None
                and destination_file.sha256 == intent["source_sha256"]
                and stage_file is None
            ):
                if (
                    prior_file is not None
                    and prior_file.sha256 != intent["prior_sha256"]
                ):
                    raise RunnerError(
                        "non-lockbox recovery prior digest mismatch is retained"
                    )
                action = "finish-committed"
            elif (
                destination_file is None
                and prior_file is not None
                and stage_file is not None
                and prior_file.sha256 == intent["prior_sha256"]
                and stage_file.sha256 == intent["source_sha256"]
            ):
                action = "restore-prior"
            elif (
                destination_file is not None
                and destination_file.sha256 == intent["prior_sha256"]
                and prior_file is None
                and stage_file is not None
                and stage_file.sha256 == intent["source_sha256"]
            ):
                action = "discard-uncommitted-stage"
            else:
                raise RunnerError(
                    "non-lockbox recovery is ambiguous; evidence retained"
                )
        plan = _NonLockboxArtifactRecoveryPlan(
            destination=target,
            parent_authority=parent_authority,
            action=action,
            destination_file=destination_file,
            intent_file=intent_file,
            prior_file=prior_file,
            stage_file=stage_file,
        )
        opened.clear()
        return plan
    finally:
        close_error = _close_owned_regular_file_authorities_once(opened)
        if close_error is not None:
            raise close_error


def _execute_non_lockbox_artifact_recovery_plan(
    plan: _NonLockboxArtifactRecoveryPlan,
) -> None:
    parent = plan.parent_authority
    _verify_held_directory_authority(parent)
    for authority in _non_lockbox_recovery_plan_files(plan):
        _verify_held_regular_file_authority(authority)
    if plan.action == "discard-stage":
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
    elif plan.action == "finish-committed":
        if plan.prior_file is not None:
            owned_prior = plan.prior_file
            plan.prior_file = None
            _safe_unlink_owned_file(owned_prior)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
    elif plan.action == "restore-prior":
        assert plan.prior_file is not None
        plan.prior_file = _renamed_held_regular_file_authority(
            plan.prior_file,
            plan.destination,
            parent_authority=parent,
        )
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
    elif plan.action == "discard-uncommitted-stage":
        assert plan.stage_file is not None
        owned_stage = plan.stage_file
        plan.stage_file = None
        _safe_unlink_owned_file(owned_stage)
        assert plan.intent_file is not None
        owned_intent = plan.intent_file
        plan.intent_file = None
        _safe_unlink_owned_file(owned_intent)
    elif plan.action != "none":
        raise RunnerError("non-lockbox recovery action changed")
    _flush_held_directory(parent)


def _reconcile_non_lockbox_artifacts(
    paths: RunnerPaths,
    authorities: _NonLockboxOutputAuthorities,
) -> None:
    _validate_non_lockbox_output_shape(
        paths,
        authorities,
        require_complete=False,
        allow_controls=True,
    )
    destinations = _non_lockbox_artifact_destinations(paths)
    groups = (
        (authorities.root, destinations[4:]),
        (authorities.cache_root, destinations[:4]),
    )
    snapshots: dict[Path, frozenset[str]] = {}
    names_by_destination: dict[Path, frozenset[str]] = {}
    for parent, fixed_destinations in groups:
        entries = _held_directory_entry_statuses(parent)
        snapshots[parent.path] = frozenset(entries)
        for destination in fixed_destinations:
            intent, prior = _replacement_control_paths(destination)
            recognized = {
                destination.name,
                _non_lockbox_artifact_stage_path(destination).name,
                intent.name,
                prior.name,
            }
            names_by_destination[destination] = frozenset(
                set(entries) & recognized
            )

    plans: list[_NonLockboxArtifactRecoveryPlan] = []
    try:
        for destination in destinations:
            parent = _non_lockbox_output_parent_for_destination(
                paths,
                destination,
                authorities,
            )
            plans.append(
                _plan_non_lockbox_artifact_destination_recovery(
                    paths,
                    destination,
                    parent_authority=parent,
                    entry_names=names_by_destination[destination],
                )
            )
        for parent, _fixed_destinations in groups:
            if frozenset(_held_directory_entry_statuses(parent)) != snapshots[
                parent.path
            ]:
                raise RunnerError(
                    "non-lockbox recovery namespace changed during planning"
                )
        for plan in plans:
            _execute_non_lockbox_artifact_recovery_plan(plan)
    finally:
        active_error = sys.exc_info()[1]
        cleanup_error: Exception | None = None
        for plan in plans:
            try:
                _close_non_lockbox_recovery_plan(plan)
            except Exception as error:
                if cleanup_error is None:
                    cleanup_error = error
        if cleanup_error is not None:
            _raise_owner_cleanup_failure(
                "non-lockbox recovery owner cleanup failed",
                cleanup_error,
                active_error=active_error,
            )
    _validate_non_lockbox_output_shape(
        paths,
        authorities,
        require_complete=False,
        allow_controls=False,
    )


@contextmanager
def _held_non_lockbox_output_authorities(
    paths: RunnerPaths,
    material_authority: _MaterialPipelineAuthority,
) -> Iterator[_NonLockboxOutputAuthorities]:
    _validate_layout(paths)
    if type(material_authority) is not _MaterialPipelineAuthority:
        raise RunnerError("material-pipeline authority is required")
    _verify_material_pipeline_authority(material_authority)
    if material_authority.state_root.path != Path(paths.state_root):
        raise RunnerError("material-pipeline state root changed")
    with ExitStack() as stack:
        root = stack.enter_context(_held_child_directory_authority(
            Path(paths.non_lockbox_root),
            material_authority.state_root,
        ))
        cache_root = stack.enter_context(_held_child_directory_authority(
            Path(paths.non_lockbox_cache_root),
            root,
        ))
        authorities = _NonLockboxOutputAuthorities(
            root=root,
            cache_root=cache_root,
        )
        _reconcile_non_lockbox_artifacts(paths, authorities)
        try:
            yield authorities
        finally:
            _verify_material_pipeline_authority(material_authority)
            _validate_non_lockbox_output_shape(
                paths,
                authorities,
                require_complete=False,
                allow_controls=False,
            )


@contextmanager
def _held_existing_non_lockbox_outputs(
    paths: RunnerPaths,
    material_authority: _MaterialPipelineAuthority,
) -> Iterator[_NonLockboxOutputAuthorities]:
    """Bind a complete committed output tree without creating or recovering it."""
    _verify_material_pipeline_authority(material_authority)
    if (
        type(material_authority) is not _MaterialPipelineAuthority
        or material_authority.state_root.path != Path(paths.state_root)
    ):
        raise RunnerError("material-pipeline state-root capability changed")
    with ExitStack() as stack:
        try:
            root = stack.enter_context(_held_child_directory_authority(
                Path(paths.non_lockbox_root),
                material_authority.state_root,
                create=False,
            ))
            cache_root = stack.enter_context(_held_child_directory_authority(
                Path(paths.non_lockbox_cache_root),
                root,
                create=False,
            ))
            authorities = _NonLockboxOutputAuthorities(
                root=root,
                cache_root=cache_root,
            )
        except (OSError, RunnerError) as error:
            raise RunnerError(
                "committed non-lockbox output root is unavailable"
            ) from error
        _validate_non_lockbox_output_shape(
            paths,
            authorities,
            require_complete=True,
            allow_controls=False,
        )
        try:
            yield authorities
        finally:
            _verify_material_pipeline_authority(material_authority)
            _validate_non_lockbox_output_shape(
                paths,
                authorities,
                require_complete=True,
                allow_controls=False,
            )


def _replace_non_lockbox_bytes_durably(
    paths: RunnerPaths,
    destination: Path,
    content: bytes,
    *,
    output_authorities: _NonLockboxOutputAuthorities,
) -> _HeldRegularFileAuthority:
    target = Path(destination)
    if (
        type(paths) is not RunnerPaths
        or type(content) is not bytes
        or target not in _non_lockbox_artifact_destinations(paths)
        or type(output_authorities) is not _NonLockboxOutputAuthorities
    ):
        raise RunnerError("non-lockbox replacement target is invalid")
    parent = _non_lockbox_output_parent_for_destination(
        paths,
        target,
        output_authorities,
    )
    _validate_non_lockbox_output_shape(
        paths,
        output_authorities,
        require_complete=False,
        allow_controls=False,
    )
    if os.name != "nt":
        raise RunnerError(
            "non-lockbox durable replacement is Windows-qualified only"
        )
    stage_path = _non_lockbox_artifact_stage_path(target)
    intent_path, prior_path = _replacement_control_paths(target)
    stage = _create_held_regular_file_authority(
        stage_path,
        content,
        parent_authority=parent,
    )
    promoted: _HeldRegularFileAuthority | None = stage
    previous: _HeldRegularFileAuthority | None = None
    intent: _HeldRegularFileAuthority | None = None
    try:
        if os.path.lexists(target):
            if os.path.lexists(intent_path) or os.path.lexists(prior_path):
                raise RunnerError(
                    "non-lockbox replacement control entry already exists"
                )
            previous = _open_owned_regular_file_authority(
                target,
                parent_authority=parent,
                delete_access=True,
            )
            intent = _create_held_regular_file_authority(
                intent_path,
                canonical_json_bytes({
                    "schema_version": _REPLACE_INTENT_SCHEMA_VERSION,
                    "destination_name": target.name,
                    "prior_name": prior_path.name,
                    "source_sha256": stage.sha256,
                    "prior_sha256": previous.sha256,
                }),
                parent_authority=parent,
            )
            previous = _renamed_held_regular_file_authority(
                previous,
                prior_path,
                parent_authority=parent,
            )
        promoted = _renamed_held_regular_file_authority(
            stage,
            target,
            parent_authority=parent,
        )
        _flush_held_directory(parent)
        _verify_held_regular_file_authority(promoted)
        if _read_held_regular_file_bytes(promoted) != content:
            raise RunnerError("non-lockbox artifact immediate readback mismatch")
        if previous is not None:
            owned_previous = previous
            previous = None
            _safe_unlink_owned_file(owned_previous)
        if intent is not None:
            owned_intent = intent
            intent = None
            _safe_unlink_owned_file(owned_intent)
        _flush_held_directory(parent)
        _verify_held_regular_file_authority(promoted)
        result = promoted
        promoted = None
        return result
    finally:
        close_error = _close_owned_regular_file_authorities_once(tuple(
            authority
            for authority in (previous, intent, promoted)
            if authority is not None
        ))
        if close_error is not None:
            raise close_error


def _validate_non_lockbox_readback_files(
    paths: RunnerPaths,
    files: tuple[_HeldRegularFileAuthority, ...],
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any], dict[str, Any]]:
    destinations = _non_lockbox_artifact_destinations(paths)
    if (
        type(files) is not tuple
        or len(files) != len(destinations)
        or tuple(authority.path for authority in files) != destinations
    ):
        raise RunnerError("non-lockbox readback file order changed")
    payloads: list[dict[str, Any]] = []
    for destination, authority in zip(destinations, files, strict=True):
        _verify_held_regular_file_authority(authority)
        payloads.append(_parse_non_lockbox_artifact_bytes(
            paths,
            destination,
            _read_held_regular_file_bytes(authority),
        ))
    artifacts = ProductionNonLockboxArtifacts(
        feature_caches={
            role: payloads[index]
            for index, role in enumerate(NONFINAL_PARTITION_ROLES)
        },
        ami_evidence=payloads[3],
        review_packet=payloads[4],
    )
    expected_bytes = _non_lockbox_payload_bytes(paths, artifacts)
    for authority, (_destination, expected) in zip(
        files,
        expected_bytes,
        strict=True,
    ):
        if _read_held_regular_file_bytes(authority) != expected:
            raise RunnerError("persisted non-lockbox artifact bytes changed")
    return (
        tuple(deepcopy(payload) for payload in payloads[:3]),
        deepcopy(payloads[3]),
        deepcopy(payloads[4]),
    )


@contextmanager
def _persist_non_lockbox_artifacts(
    paths: RunnerPaths,
    artifacts: ProductionNonLockboxArtifacts,
    *,
    material_authority: _MaterialPipelineAuthority,
    output_authorities: _NonLockboxOutputAuthorities,
) -> Iterator[_PersistedNonLockboxReadback]:
    _verify_material_pipeline_authority(material_authority)
    if type(output_authorities) is not _NonLockboxOutputAuthorities:
        raise RunnerError("non-lockbox output authority type changed")
    if material_authority.state_root.path != Path(paths.state_root):
        raise RunnerError("material-pipeline state root changed")
    payload_bytes = _non_lockbox_payload_bytes(paths, artifacts)
    files: list[_HeldRegularFileAuthority] = []
    try:
        for destination, content in payload_bytes:
            files.append(_replace_non_lockbox_bytes_durably(
                paths,
                destination,
                content,
                output_authorities=output_authorities,
            ))
        held_files = tuple(files)
        _validate_non_lockbox_output_shape(
            paths,
            output_authorities,
            require_complete=True,
            allow_controls=False,
        )
        feature_caches, ami_evidence, review_packet = (
            _validate_non_lockbox_readback_files(paths, held_files)
        )
        readback = _PersistedNonLockboxReadback(
            feature_caches=feature_caches,
            ami_evidence=ami_evidence,
            review_packet=review_packet,
            files=held_files,
        )
        try:
            yield readback
        finally:
            _verify_material_pipeline_authority(material_authority)
            for authority in held_files:
                _verify_held_regular_file_authority(authority)
            replay = _validate_non_lockbox_readback_files(paths, held_files)
            if replay != (feature_caches, ami_evidence, review_packet):
                raise RunnerError("non-lockbox retained readback changed")
            _validate_non_lockbox_output_shape(
                paths,
                output_authorities,
                require_complete=True,
                allow_controls=False,
            )
    finally:
        active_error = sys.exc_info()[1]
        close_error = _close_owned_regular_file_authorities_once(files)
        files.clear()
        if close_error is not None:
            _raise_owner_cleanup_failure(
                "non-lockbox retained file cleanup failed",
                close_error,
                active_error=active_error,
            )


def _verify_complete_preflight_readback_authority(
    paths: RunnerPaths,
    output_authorities: _PreflightOutputAuthorities,
    readback_authority: _PersistedPreflightReadback,
) -> None:
    try:
        if type(output_authorities) is not _PreflightOutputAuthorities:
            raise RunnerError("preflight output authority type changed")
        if type(readback_authority) is not _PersistedPreflightReadback:
            raise RunnerError("persisted preflight readback authority changed")
        held_roots = (
            output_authorities.inputs_root,
            output_authorities.split_root,
            output_authorities.preflight_root,
        )
        expected_roots = (
            Path(paths.input_ledger_path).parent,
            Path(paths.split_manifest_path).parent,
            Path(paths.preflight_cache_root),
        )
        if any(
            type(authority) is not _HeldDirectoryAuthority
            or authority.path != expected
            for authority, expected in zip(held_roots, expected_roots, strict=True)
        ):
            raise RunnerError("preflight output authority aggregate changed")
        files = readback_authority.files
        expected_paths = _preflight_artifact_destinations(paths)
        if (
            type(files) is not tuple
            or len(files) != len(expected_paths)
            or any(
                type(authority) is not _HeldRegularFileAuthority
                or authority.path != expected
                for authority, expected in zip(files, expected_paths, strict=True)
            )
        ):
            raise RunnerError("persisted preflight file aggregate changed")
        expected_parents = (
            held_roots[0],
            held_roots[1],
            held_roots[2],
            held_roots[2],
            held_roots[2],
        )
        if any(
            authority.path.parent != parent.path
            for authority, parent in zip(files, expected_parents, strict=True)
        ):
            raise RunnerError("persisted preflight parent relationship changed")
        for authority in held_roots:
            _verify_held_directory_authority(authority)
        for authority in files:
            _verify_held_regular_file_authority(authority)
    except RunnerError:
        raise
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise RunnerError("preflight readback capability is unavailable") from error


def _load_bound_partition_authority(
    paths: RunnerPaths,
    *,
    role: str,
    expected_split_manifest_file_sha256: str,
    material_authority: _MaterialPipelineAuthority,
    output_authorities: _PreflightOutputAuthorities,
    readback_authority: _PersistedPreflightReadback,
) -> Any:
    if type(role) is not str or role not in NONFINAL_PARTITION_ROLES:
        raise RunnerError("non-lockbox partition role is invalid")
    expected_digest = _validate_digest(
        expected_split_manifest_file_sha256,
        "split manifest file",
    )
    _verify_material_pipeline_authority(material_authority)
    _verify_complete_preflight_readback_authority(
        paths,
        output_authorities,
        readback_authority,
    )
    files = readback_authority.files
    manifest_file = files[1]
    cache_index = 2 + NONFINAL_PARTITION_ROLES.index(role)
    cache_file = files[cache_index]
    if (
        manifest_file.path != Path(paths.split_manifest_path)
        or cache_file.path != Path(paths.partition_authority_cache_path(role))
    ):
        raise RunnerError("bound partition path or role changed")
    _verify_held_regular_file_authority(manifest_file)
    _verify_held_regular_file_authority(cache_file)
    if manifest_file.sha256 != expected_digest:
        raise RunnerError("split manifest file anchor changed")
    try:
        manifest = validate_phase_b_split_manifest(
            _load_json_object_bytes(
                _read_held_regular_file_bytes(manifest_file),
                "bound split manifest",
            )
        )
        cache = validate_phase_b_partition_authority_cache(
            _load_json_object_bytes(
                _read_held_regular_file_bytes(cache_file),
                f"bound {role} cache",
            ),
            manifest,
            expected_role=role,
        )
        from scripts import emotion_state_phase_b_evaluation as evaluation

        restored = evaluation.restore_validated_partition_authority_cache(
            cache,
            manifest,
            role=role,
        )
        records = evaluation.validated_partition_records(restored, role=role)
        if not records:
            raise ValueError("bound partition records are empty")
        payload = restored.to_payload()
        if (
            payload["partition_role"] != role
            or payload["configuration_sha256"] != manifest["configuration_sha256"]
            or payload["split_manifest_sha256"] != manifest["split_manifest_sha256"]
            or payload["assignment_sha256"] != manifest["assignment_sha256"]
            or payload["partition_authority_sha256"]
            != manifest["partition_authority_sha256"][role]
        ):
            raise ValueError("bound partition authority link changed")
    except (TypeError, ValueError) as error:
        raise RunnerError(f"bound partition authority is invalid: {error}") from error
    _verify_complete_preflight_readback_authority(
        paths,
        output_authorities,
        readback_authority,
    )
    return restored


@contextmanager
def _held_existing_preflight_outputs(
    paths: RunnerPaths,
    material_authority: _MaterialPipelineAuthority,
) -> Iterator[_PreflightOutputAuthorities]:
    _verify_material_pipeline_authority(material_authority)
    roots = (
        Path(paths.input_ledger_path).parent,
        Path(paths.split_manifest_path).parent,
        Path(paths.preflight_cache_root),
    )
    with ExitStack() as stack:
        try:
            authorities = _PreflightOutputAuthorities(*(
                stack.enter_context(_held_directory_authority(path))
                for path in roots
            ))
        except (OSError, RunnerError) as error:
            raise RunnerError("committed checkpoint output root is unavailable") from error
        _validate_preflight_output_shape(
            paths,
            authorities,
            require_complete=True,
            allow_controls=False,
        )
        yield authorities
        _validate_preflight_output_shape(
            paths,
            authorities,
            require_complete=True,
            allow_controls=False,
        )


@contextmanager
def _read_committed_preflight_checkpoint(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
    committed_state_authority: _HeldCommittedStateAuthority,
) -> Iterator[_CommittedPreflightReadback]:
    try:
        if type(committed_state_authority) is not _HeldCommittedStateAuthority:
            raise RunnerError("committed state authority type changed")
        if (
            type(committed_state_authority._file_owner)
            is not _RegularFileAuthorityOwner
            or committed_state_authority._file_owner.peek()
            is not committed_state_authority.file
        ):
            raise RunnerError("committed state owner changed before preflight readback")
        _verify_material_pipeline_authority(material_authority)
        _verify_held_regular_file_authority(committed_state_authority.file)
        state, state_bytes = _state_from_held_file(committed_state_authority.file)
        if (
            state != committed_state_authority.state
            or state_bytes != committed_state_authority.canonical_bytes
            or state["phase"] == "initialized"
        ):
            raise RunnerError("committed state capability changed")
        if (
            state["configuration_sha256"]
            != EXPECTED_STATIC_FILE_SHA256["configuration_sha256"]
            or state["environment_lock_sha256"]
            != EXPECTED_STATIC_FILE_SHA256["environment_lock_sha256"]
        ):
            raise RunnerError("committed state static anchor changed")
        with _held_existing_preflight_outputs(
            paths,
            material_authority,
        ) as output_authorities, ExitStack() as stack:
            files = tuple(
                stack.enter_context(_held_regular_file(path))
                for path in _preflight_artifact_destinations(paths)
            )
            if (
                files[0].sha256 != state["input_ledger_sha256"]
                or files[1].sha256 != state["split_manifest_sha256"]
            ):
                raise RunnerError("committed checkpoint file anchor changed")
            ledger, manifest, restored = _validate_and_restore_readback_files(
                paths,
                files,
            )
            artifacts = _PersistedPreflightReadback(
                input_ledger=ledger,
                split_manifest=manifest,
                files=files,
            )
            _assert_closed_environment()
            for authority in files:
                _verify_held_regular_file_authority(authority)
            _verify_held_regular_file_authority(committed_state_authority.file)
            _validate_state_root_allowlist(
                paths,
                material_authority.state_root,
                allow_state_controls=False,
            )
            readback = _CommittedPreflightReadback(
                state=state,
                state_file=committed_state_authority.file,
                artifacts=artifacts,
                restored=restored,
            )
            yield readback
            for authority in files:
                _verify_held_regular_file_authority(authority)
            remaining_state_file = committed_state_authority._file_owner.peek()
            if remaining_state_file is not None:
                if remaining_state_file is not committed_state_authority.file:
                    raise RunnerError(
                        "committed state owner changed after preflight readback"
                    )
                _verify_held_regular_file_authority(remaining_state_file)
    except RunnerError as error:
        if "already complete" in str(error):
            raise
        raise RunnerError(f"committed checkpoint integrity failure: {error}") from error


def _validate_runner_non_lockbox_role_algebra(
    preflight_readback: _CommittedPreflightReadback,
) -> tuple[
    dict[str, Any],
    dict[str, "ValidatedPartitionAuthority"],
    dict[str, tuple[Any, ...]],
]:
    from scripts import emotion_state_phase_b_evaluation as evaluation

    if type(preflight_readback) is not _CommittedPreflightReadback:
        raise RunnerError("committed preflight readback type changed")
    if (
        type(preflight_readback.restored) is not tuple
        or len(preflight_readback.restored) != len(NONFINAL_PARTITION_ROLES)
        or len({id(item) for item in preflight_readback.restored})
        != len(NONFINAL_PARTITION_ROLES)
        or any(
            type(item) is not evaluation.ValidatedPartitionAuthority
            for item in preflight_readback.restored
        )
    ):
        raise RunnerError("runner non-lockbox authority aggregate changed")
    try:
        manifest = validate_phase_b_split_manifest(
            deepcopy(preflight_readback.artifacts.split_manifest)
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"runner split authority is invalid: {error}") from error
    authorities = dict(zip(
        NONFINAL_PARTITION_ROLES,
        preflight_readback.restored,
        strict=True,
    ))
    if tuple(authorities) != tuple(EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS):
        raise RunnerError("runner non-lockbox role order changed")
    authority_commitments = manifest.get("partition_authority_sha256")
    if (
        type(authority_commitments) is not dict
        or set(authority_commitments) != set(NONFINAL_PARTITION_ROLES)
    ):
        raise RunnerError("runner split role commitments changed")
    records_by_role: dict[str, tuple[Any, ...]] = {}
    for role in NONFINAL_PARTITION_ROLES:
        authority = authorities[role]
        payload = authority.to_payload()
        expected_count = EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
        records = evaluation.validated_partition_records(authority, role=role)
        if (
            type(payload) is not dict
            or payload.get("partition_role") != role
            or type(payload.get("eligible_record_count")) is not int
            or payload["eligible_record_count"] != expected_count
            or payload.get("configuration_sha256")
            != manifest["configuration_sha256"]
            or payload.get("split_manifest_sha256")
            != manifest["split_manifest_sha256"]
            or payload.get("assignment_sha256")
            != manifest["assignment_sha256"]
            or payload.get("partition_authority_sha256")
            != authority_commitments[role]
            or type(records) is not tuple
            or len(records) != expected_count
            or any(
                hasattr(record, "project_relative_path")
                or hasattr(record.label_record, "project_relative_path")
                for record in records
            )
        ):
            raise RunnerError(
                f"runner {role} authority does not match frozen role algebra"
            )
        records_by_role[role] = records
    final_commitment = manifest.get("final_lockbox_commitment")
    nonfinal_count = sum(
        len(records_by_role[role]) for role in NONFINAL_PARTITION_ROLES
    )
    if (
        type(final_commitment) is not dict
        or type(final_commitment.get("eligible_record_count")) is not int
        or final_commitment["eligible_record_count"]
        != EXPECTED_PRODUCTION_FINAL_LOCKBOX_RECORD_COUNT
        or type(manifest.get("eligible_record_count")) is not int
        or manifest["eligible_record_count"]
        != EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT
        or type(nonfinal_count) is not int
        or nonfinal_count != EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT
        or type(nonfinal_count + final_commitment["eligible_record_count"])
        is not int
        or nonfinal_count + final_commitment["eligible_record_count"]
        != EXPECTED_PRODUCTION_ELIGIBLE_RECORD_COUNT
        or "final_lockbox" in authorities
        or "final_lockbox" in records_by_role
    ):
        raise RunnerError(
            "runner role algebra must be exactly 2491/959/939 plus 2181"
        )
    return deepcopy(manifest), authorities, records_by_role


def _validate_runner_non_lockbox_source_derivation_inputs(
    tracked_authority: TrackedPublicAuthority,
    records_by_role: Mapping[str, tuple[Any, ...]],
) -> None:
    if (
        type(tracked_authority) is not TrackedPublicAuthority
        or type(records_by_role) is not dict
        or tuple(records_by_role) != NONFINAL_PARTITION_ROLES
        or any(type(records_by_role[role]) is not tuple for role in records_by_role)
        or any(
            len(records_by_role[role])
            != EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
            for role in NONFINAL_PARTITION_ROLES
        )
    ):
        raise RunnerError("runner source derivation authority changed")


def _derive_runner_non_lockbox_audio_source_identities(
    tracked_authority: TrackedPublicAuthority,
    records_by_role: Mapping[str, tuple[Any, ...]],
) -> dict[str, tuple[SourceByteIdentity, ...]]:
    _validate_runner_non_lockbox_source_derivation_inputs(
        tracked_authority,
        records_by_role,
    )
    audio_identities = tracked_authority.crema_audio
    if type(audio_identities) is not tuple or len(audio_identities) != 7441:
        raise RunnerError("runner CREMA source authority count changed")
    by_stem: dict[str, SourceByteIdentity] = {}
    audio_paths: set[str] = set()
    for source in audio_identities:
        if type(source) is not SourceByteIdentity:
            raise RunnerError("runner CREMA source identity type changed")
        path = source.project_relative_path
        if (
            type(path) is not str
            or not path.startswith(_CREMA_AUDIO_SOURCE_PREFIX)
            or not path.endswith(".wav")
            or "\\" in path
            or path in audio_paths
        ):
            raise RunnerError("runner CREMA source path changed")
        stem = path[len(_CREMA_AUDIO_SOURCE_PREFIX):-4]
        if not stem or "/" in stem or stem in by_stem:
            raise RunnerError("runner CREMA source stem changed")
        _validate_digest(source.sha256, "runner CREMA source")
        if type(source.size_bytes) is not int or source.size_bytes <= 0:
            raise RunnerError("runner CREMA source size changed")
        audio_paths.add(path)
        by_stem[stem] = source

    selected_audio: dict[str, tuple[SourceByteIdentity, ...]] = {}
    consumed: set[str] = set()
    for role in NONFINAL_PARTITION_ROLES:
        expected_count = EXPECTED_PRODUCTION_PARTITION_RECORD_COUNTS[role]
        sources: list[SourceByteIdentity] = []
        for record in records_by_role[role]:
            label_record = getattr(record, "label_record", None)
            stem = getattr(label_record, "clip_stem", None)
            source = by_stem.get(stem)
            if (
                type(stem) is not str
                or source is None
                or source.sha256 != getattr(record, "audio_sha256", None)
                or source.size_bytes != getattr(record, "audio_size_bytes", None)
                or stem in consumed
            ):
                raise RunnerError(
                    f"runner {role} audio source does not match sealed authority"
                )
            consumed.add(stem)
            sources.append(source)
        if len(sources) != expected_count:
            raise RunnerError(f"runner {role} audio source count changed")
        selected_audio[role] = tuple(sources)
    if len(consumed) != EXPECTED_PRODUCTION_NONFINAL_RECORD_COUNT:
        raise RunnerError("runner non-lockbox audio source count changed")
    return selected_audio


def _derive_runner_non_lockbox_ami_source_identities(
    tracked_authority: TrackedPublicAuthority,
    records_by_role: Mapping[str, tuple[Any, ...]],
) -> tuple[SourceByteIdentity, ...]:
    _validate_runner_non_lockbox_source_derivation_inputs(
        tracked_authority,
        records_by_role,
    )
    ami_identities = tracked_authority.ami_files
    if type(ami_identities) is not tuple or len(ami_identities) != 2074:
        raise RunnerError("runner AMI source authority count changed")
    selected_ami: list[SourceByteIdentity] = []
    excluded: set[str] = set()
    adjacency_pair_count = 0
    ami_paths: set[str] = set()
    family_counts = {
        "meetings": 0,
        "participants": 0,
        "words": 0,
        "segments": 0,
        "dialogue_acts": 0,
    }
    direct_families = (
        ("words", f"{_AMI_EXTRACTED_SOURCE_ROOT}words/", ".words.xml"),
        ("segments", f"{_AMI_EXTRACTED_SOURCE_ROOT}segments/", ".segments.xml"),
        (
            "dialogue_acts",
            f"{_AMI_EXTRACTED_SOURCE_ROOT}dialogueActs/",
            ".dialog-act.xml",
        ),
        (
            "adjacency_pairs",
            f"{_AMI_EXTRACTED_SOURCE_ROOT}dialogueActs/",
            ".adjacency-pairs.xml",
        ),
    )
    for source in ami_identities:
        if type(source) is not SourceByteIdentity:
            raise RunnerError("runner AMI source identity type changed")
        path = source.project_relative_path
        if (
            type(path) is not str
            or not path.startswith(_AMI_SOURCE_ROOT)
            or "\\" in path
            or path in ami_paths
        ):
            raise RunnerError("runner AMI source path changed")
        _validate_digest(source.sha256, "runner AMI source")
        if type(source.size_bytes) is not int or source.size_bytes <= 0:
            raise RunnerError("runner AMI source size changed")
        ami_paths.add(path)
        family: str | None = None
        if path == _AMI_MEETING_UNIVERSE_SOURCE:
            family = "meetings"
        elif path == _AMI_PARTICIPANTS_SOURCE:
            family = "participants"
        else:
            for candidate, prefix, suffix in direct_families:
                basename = path[len(prefix):] if path.startswith(prefix) else ""
                if (
                    basename
                    and "/" not in basename
                    and basename.endswith(suffix)
                    and len(basename) > len(suffix)
                ):
                    family = candidate
                    break
        if family is None and path in _AMI_EXCLUDED_SOURCES:
            excluded.add(path)
            continue
        if family == "adjacency_pairs":
            adjacency_pair_count += 1
            continue
        if family is None:
            raise RunnerError("runner AMI source is not in a frozen family")
        family_counts[family] += 1
        selected_ami.append(source)
    if (
        family_counts
        != {
            "meetings": 1,
            "participants": 1,
            "words": 687,
            "segments": 687,
            "dialogue_acts": 556,
        }
        or excluded != set(_AMI_EXCLUDED_SOURCES)
        or adjacency_pair_count != 139
        or len(selected_ami) != EXPECTED_AMI_SELECTED_SOURCE_COUNT
    ):
        raise RunnerError("runner AMI selected source families changed")
    return tuple(selected_ami)


def _derive_runner_non_lockbox_source_identities(
    tracked_authority: TrackedPublicAuthority,
    records_by_role: Mapping[str, tuple[Any, ...]],
) -> tuple[
    dict[str, tuple[SourceByteIdentity, ...]],
    tuple[SourceByteIdentity, ...],
]:
    return (
        _derive_runner_non_lockbox_audio_source_identities(
            tracked_authority,
            records_by_role,
        ),
        _derive_runner_non_lockbox_ami_source_identities(
            tracked_authority,
            records_by_role,
        ),
    )


@contextmanager
def _read_committed_non_lockbox_checkpoint(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
    committed_state_authority: _HeldCommittedStateAuthority,
    preflight_readback: _CommittedPreflightReadback,
) -> Iterator[_PersistedNonLockboxReadback]:
    """Authenticate and replay an existing checkpoint without source reads/writes."""
    try:
        if type(committed_state_authority) is not _HeldCommittedStateAuthority:
            raise RunnerError("committed state authority type changed")
        if (
            type(committed_state_authority._file_owner)
            is not _RegularFileAuthorityOwner
            or committed_state_authority._file_owner.peek()
            is not committed_state_authority.file
        ):
            raise RunnerError(
                "committed state owner changed before non-lockbox readback"
            )
        if type(preflight_readback) is not _CommittedPreflightReadback:
            raise RunnerError("committed preflight readback type changed")
        if (
            preflight_readback.state_file is not committed_state_authority.file
            or preflight_readback.state != committed_state_authority.state
        ):
            raise RunnerError("committed preflight/state capability changed")
        _verify_material_pipeline_authority(material_authority)
        _verify_held_regular_file_authority(committed_state_authority.file)
        state, state_bytes = _state_from_held_file(
            committed_state_authority.file
        )
        if (
            state != committed_state_authority.state
            or state_bytes != committed_state_authority.canonical_bytes
            or state["phase"] not in {
                "non_lockbox_complete",
                "lockbox_complete",
                "awaiting_acceptance",
                "accepted",
                "rejected",
            }
            or state["non_lockbox_packet_sha256"] == UNSET_DIGEST
        ):
            raise RunnerError("committed non-lockbox state capability changed")
        if (
            state["configuration_sha256"]
            != EXPECTED_STATIC_FILE_SHA256["configuration_sha256"]
            or state["environment_lock_sha256"]
            != EXPECTED_STATIC_FILE_SHA256["environment_lock_sha256"]
        ):
            raise RunnerError("committed non-lockbox static anchor changed")

        preflight_files = preflight_readback.artifacts.files
        ledger, manifest, replayed_preflight = (
            _validate_and_restore_readback_files(paths, preflight_files)
        )
        if (
            ledger != preflight_readback.artifacts.input_ledger
            or manifest != preflight_readback.artifacts.split_manifest
            or len(replayed_preflight) != len(NONFINAL_PARTITION_ROLES)
            or len(preflight_readback.restored) != len(NONFINAL_PARTITION_ROLES)
            or any(
                actual.to_payload() != retained.to_payload()
                for actual, retained in zip(
                    replayed_preflight,
                    preflight_readback.restored,
                    strict=True,
                )
            )
        ):
            raise RunnerError("committed preflight semantic replay changed")

        configuration = validate_config(deepcopy(EXPECTED_CONFIG))
        environment_lock = validate_environment_lock(
            deepcopy(EXPECTED_ENVIRONMENT_LOCK)
        )
        feature_schema = validate_feature_schema(
            deepcopy(EXPECTED_FEATURE_SCHEMA)
        )
        split_schema = validate_split_schema(deepcopy(EXPECTED_SPLIT_SCHEMA))
        try:
            configuration, feature_schema = (
                validate_config_feature_schema_binding(
                    configuration,
                    feature_schema,
                )
            )
        except (TypeError, ValueError) as error:
            raise RunnerError(
                "committed non-lockbox config/schema cross-binding failed: "
                f"{error}"
            ) from error
        authorities = dict(zip(
            NONFINAL_PARTITION_ROLES,
            preflight_readback.restored,
            strict=True,
        ))

        with _held_existing_non_lockbox_outputs(
            paths,
            material_authority,
        ) as output_authorities, ExitStack() as stack:
            files = tuple(
                stack.enter_context(_held_regular_file(path))
                for path in _non_lockbox_artifact_destinations(paths)
            )
            if files[-1].sha256 != state["non_lockbox_packet_sha256"]:
                raise RunnerError("committed non-lockbox packet anchor changed")
            feature_caches, ami_evidence, review_packet = (
                _validate_non_lockbox_readback_files(paths, files)
            )
            restored = restore_production_non_lockbox_artifacts(
                authorities=authorities,
                split_manifest=deepcopy(manifest),
                feature_caches={
                    role: deepcopy(payload)
                    for role, payload in zip(
                        NONFINAL_PARTITION_ROLES,
                        feature_caches,
                        strict=True,
                    )
                },
                ami_evidence=deepcopy(ami_evidence),
                review_packet=deepcopy(review_packet),
                configuration=deepcopy(configuration),
                environment_lock=deepcopy(environment_lock),
                feature_schema=deepcopy(feature_schema),
                split_schema=deepcopy(split_schema),
            )
            expected_bytes = tuple(
                _non_lockbox_artifact_json_bytes(payload)
                for payload in (
                    *(restored.feature_caches[role]
                      for role in NONFINAL_PARTITION_ROLES),
                    restored.ami_evidence,
                    restored.review_packet,
                )
            )
            retained_bytes = tuple(
                _read_held_regular_file_bytes(file) for file in files
            )
            if expected_bytes != retained_bytes:
                raise RunnerError(
                    "committed non-lockbox semantic replay changed bytes"
                )
            validate_installed_environment_identity()
            _assert_closed_environment()
            _verify_material_pipeline_authority(material_authority)
            _verify_held_regular_file_authority(
                committed_state_authority.file
            )
            for file in (*preflight_files, *files):
                _verify_held_regular_file_authority(file)
            _validate_non_lockbox_output_shape(
                paths,
                output_authorities,
                require_complete=True,
                allow_controls=False,
            )
            readback = _PersistedNonLockboxReadback(
                feature_caches=feature_caches,
                ami_evidence=ami_evidence,
                review_packet=review_packet,
                files=files,
            )
            yield readback
            if tuple(
                _read_held_regular_file_bytes(file) for file in files
            ) != retained_bytes:
                raise RunnerError("committed non-lockbox retained bytes changed")
            for file in (*preflight_files, *files):
                _verify_held_regular_file_authority(file)
            remaining_state = committed_state_authority._file_owner.peek()
            if remaining_state is not committed_state_authority.file:
                raise RunnerError(
                    "committed state owner changed after non-lockbox readback"
                )
            _verify_held_regular_file_authority(remaining_state)
    except RunnerError as error:
        raise RunnerError(
            f"committed non-lockbox checkpoint integrity failure: {error}"
        ) from error
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise RunnerError(
            "committed non-lockbox checkpoint integrity failure"
        ) from error


def _validate_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise RunnerError(f"{field} must be an uppercase SHA-256")
    return value


def _validate_transaction_id(value: Any) -> str:
    if not isinstance(value, str) or _TRANSACTION_ID_PATTERN.fullmatch(value) is None:
        raise RunnerError("invalid publication transaction id")
    return value


def _validate_receipt_name(value: Any) -> str:
    if (
        not isinstance(value, str)
        or _RECEIPT_NAME_PATTERN.fullmatch(value) is None
        or value in {JOURNAL_NAME, LOCK_NAME}
    ):
        raise RunnerError("invalid publication receipt name")
    return value


def _absolute_lexical(path: Path, project_root: Path) -> Path:
    candidate = Path(path)
    if any(part == ".." for part in candidate.parts):
        raise RunnerError("parent traversal is blocked")
    try:
        return Path(
            os.path.abspath(candidate if candidate.is_absolute() else project_root / candidate)
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise RunnerError("path could not be resolved safely") from error


def _contains_private_component(path: Path) -> bool:
    return any(part.casefold() in PRIVATE_COMPONENTS for part in path.parts)


def _is_link_or_reparse(path: Path, status: os.stat_result | Any) -> bool:
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(status.st_mode) or bool(
        getattr(status, "st_file_attributes", 0) & reparse_flag
    )


def _inspect_component_chain(
    path: Path,
    *,
    trusted_root: Path,
    final_kind: str | None = None,
    require_final: bool = False,
) -> bool:
    target = Path(path)
    anchor = Path(trusted_root)
    try:
        target.relative_to(anchor)
    except ValueError as error:
        raise RunnerError("path is outside its allowed root") from error
    try:
        anchor_status = os.lstat(anchor)
    except OSError as error:
        raise RunnerError("trusted root could not be inspected") from error
    if _is_link_or_reparse(anchor, anchor_status):
        raise RunnerError("trusted root is a symlink or reparse point")
    if not stat.S_ISDIR(anchor_status.st_mode):
        raise RunnerError("trusted root is not a directory")

    current = anchor
    relative = target.relative_to(anchor)
    for index, part in enumerate(relative.parts):
        current /= part
        is_final = index == len(relative.parts) - 1
        try:
            current_status = os.lstat(current)
        except FileNotFoundError:
            if require_final or not is_final:
                if require_final:
                    raise RunnerError("required path is missing")
            return False
        except OSError as error:
            raise RunnerError("path component could not be inspected") from error
        if _is_link_or_reparse(current, current_status):
            raise RunnerError("path component is a symlink or reparse point")
        if not is_final and not stat.S_ISDIR(current_status.st_mode):
            raise RunnerError("intermediate path component is not a directory")
        if is_final and final_kind == "file" and not stat.S_ISREG(
            current_status.st_mode
        ):
            raise RunnerError("required path is not a regular file")
        if is_final and final_kind == "directory" and not stat.S_ISDIR(
            current_status.st_mode
        ):
            raise RunnerError("required root is not a directory")
    return True


def _cache_path_identity_proof(path: Path, trusted_root: Path) -> None:
    target = Path(path)
    root = Path(trusted_root)
    proof: list[tuple[str, int, int]] = []
    components = (root,) + tuple(
        root.joinpath(*target.relative_to(root).parts[:index])
        for index in range(1, len(target.relative_to(root).parts) + 1)
    )
    for component in components:
        try:
            status = os.stat(component, follow_symlinks=False)
        except FileNotFoundError:
            break
        if _is_link_or_reparse(component, status):
            raise RunnerError("path proof contains a symlink or reparse point")
        proof.append((str(component), status.st_dev, status.st_ino))
    _PATH_IDENTITY_PROOFS[str(target)] = tuple(proof)


def _verify_cached_path_proof(path: Path) -> None:
    proof = _PATH_IDENTITY_PROOFS.get(str(Path(path)))
    if proof is None:
        return
    for component, expected_device, expected_inode in proof:
        try:
            status = os.stat(component, follow_symlinks=False)
        except OSError as error:
            raise RunnerError("path identity proof is no longer reachable") from error
        if (
            _is_link_or_reparse(Path(component), status)
            or (status.st_dev, status.st_ino)
            != (expected_device, expected_inode)
        ):
            raise RunnerError("path component identity changed before open")


def _require_mutation_path_proof(path: Path) -> None:
    """Require a cached parent authority before mutating a directory entry."""
    target = Path(path)
    if str(target) not in _PATH_IDENTITY_PROOFS:
        parent = target.parent
        parent_proof = _PATH_IDENTITY_PROOFS.get(str(parent))
        if parent_proof is None:
            for proof in _PATH_IDENTITY_PROOFS.values():
                if proof and Path(proof[-1][0]) == parent:
                    parent_proof = proof
                    break
        if parent_proof is None:
            raise RunnerError("trusted parent identity is not cached")
        _PATH_IDENTITY_PROOFS[str(target)] = tuple(parent_proof)
    _verify_cached_path_proof(target)


def _bind_mutated_entry(path: Path, *, present: bool) -> None:
    """Refresh a cached proof after this runner intentionally changes an entry."""
    target = Path(path)
    proof = _PATH_IDENTITY_PROOFS.get(str(target), ())
    parent_proof = tuple(item for item in proof if Path(item[0]) != target)
    if present:
        status = os.stat(target, follow_symlinks=False)
        if _is_link_or_reparse(target, status):
            raise RunnerError("mutated entry became a link or reparse point")
        parent_proof += ((str(target), status.st_dev, status.st_ino),)
    _PATH_IDENTITY_PROOFS[str(target)] = parent_proof


def _seed_sibling_path_proof(reference: Path, sibling: Path) -> None:
    reference = Path(reference)
    sibling = Path(sibling)
    if reference.parent != sibling.parent:
        raise RunnerError("sibling path proof requires one trusted parent")
    proof = _PATH_IDENTITY_PROOFS.get(str(reference))
    if proof is None:
        raise RunnerError("reference path identity is not cached")
    parent_proof = tuple(
        item for item in proof if Path(item[0]) != reference
    )
    if not any(Path(component) == sibling.parent for component, _, _ in parent_proof):
        raise RunnerError("trusted sibling parent identity is not cached")
    _PATH_IDENTITY_PROOFS[str(sibling)] = parent_proof
    if os.path.lexists(sibling):
        _bind_mutated_entry(sibling, present=True)


@contextmanager
def _trusted_parent_handles(
    path: Path,
    *,
    include_target: bool = True,
    mutation: bool = False,
) -> Iterator[_DirectoryAuthority]:
    target = Path(path)
    proof = _PATH_IDENTITY_PROOFS.get(str(target), ())
    parent_proof = [item for item in proof if Path(item[0]) != target]
    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target.parent, flags)
        try:
            expected = next(
                (
                    (device, inode)
                    for component, device, inode in parent_proof
                    if Path(component) == target.parent
                ),
                None,
            )
            actual = os.fstat(descriptor)
            if expected is not None and (actual.st_dev, actual.st_ino) != expected:
                raise RunnerError("trusted parent handle identity changed")
            yield _DirectoryAuthority(
                path=target.parent,
                posix_descriptor=descriptor,
            )
        finally:
            os.close(descriptor)
        return

    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    close = kernel32.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    handles: list[int] = []
    parent_handle: int | None = None
    invalid = wintypes.HANDLE(-1).value
    try:
        held_proof = proof if include_target else tuple(parent_proof)
        for component, _device, _inode in held_proof:
            is_parent = Path(component) == target.parent
            handle = create_file(
                component,
                (
                    0x80000000 | 0x40000000
                    if is_parent and mutation
                    else 0x80000000
                ),
                0x00000001 | 0x00000002,  # exclude FILE_SHARE_DELETE
                None,
                3,
                0x02000000 | 0x00200000,
                None,
            )
            if handle == invalid:
                raise OSError(
                    ctypes.get_last_error(),
                    "unable to hold trusted directory component",
                )
            handles.append(handle)
            if is_parent:
                parent_handle = handle
        if parent_handle is None:
            raise RunnerError("trusted parent authority handle is unavailable")
        _verify_cached_path_proof(target)
        yield _DirectoryAuthority(
            path=target.parent,
            windows_handle=parent_handle,
        )
    finally:
        for handle in reversed(handles):
            close(handle)


def _safe_path(
    path: Path,
    *,
    allowed_root: Path,
    project_root: Path,
    final_kind: str | None = None,
    require_final: bool = False,
) -> Path:
    project = _absolute_lexical(Path(project_root), Path(project_root))
    allowed = _absolute_lexical(Path(allowed_root), project)
    candidate = _absolute_lexical(Path(path), project)
    if (
        _contains_private_component(project)
        or _contains_private_component(allowed)
        or _contains_private_component(candidate)
    ):
        raise RunnerError("private path component is blocked")
    try:
        allowed.relative_to(project)
    except ValueError as error:
        raise RunnerError("allowed root must stay inside project root") from error
    try:
        candidate.relative_to(allowed)
    except ValueError as error:
        raise RunnerError("path is outside its allowed root") from error
    _inspect_component_chain(allowed, trusted_root=project)
    _inspect_component_chain(
        candidate,
        trusted_root=project,
        final_kind=final_kind,
        require_final=require_final,
    )
    _cache_path_identity_proof(candidate, project)
    return candidate


def _validate_layout(paths: RunnerPaths) -> None:
    project = _absolute_lexical(Path(paths.project_root), Path(paths.project_root))
    input_root = _absolute_lexical(Path(paths.input_root), project)
    state_root = _absolute_lexical(Path(paths.state_root), project)
    canonical_root = _absolute_lexical(Path(paths.canonical_root), project)
    if any(
        part.casefold() in REPOSITORY_METADATA_COMPONENTS
        for candidate in (state_root, canonical_root)
        for part in candidate.parts
    ):
        raise RunnerError("repository metadata cannot be a runner output root")
    if paths.authority == "production":
        if paths.lockbox_result_path is not None:
            raise RunnerError(
                "production lockbox-result capability must stay inert"
            )
        prescribed = RunnerPaths.production()
        exact_fields = (
            "project_root",
            "input_root",
            "state_root",
            "canonical_root",
            "config_path",
            "environment_lock_path",
            "feature_schema_path",
            "split_schema_path",
            "split_manifest_path",
            "input_ledger_path",
            "non_lockbox_packet_path",
            "public_material_root",
        )
        if any(
            _absolute_lexical(Path(getattr(paths, field)), project)
            != _absolute_lexical(Path(getattr(prescribed, field)), ROOT)
            for field in exact_fields
        ):
            raise RunnerError("production root authority does not match prescribed paths")
    elif paths.authority == "injected-test":
        try:
            project.relative_to(ROOT)
        except ValueError:
            pass
        else:
            raise RunnerError("injected test roots cannot target the real repository")
        expected_input_ledger = state_root / "inputs" / "input-ledger.json"
        expected_split_manifest = (
            state_root / "split" / "validated-split-manifest.json"
        )
        expected_non_lockbox_packet = (
            state_root / "non-lockbox" / "non-lockbox-packet.json"
        )
        if (
            _absolute_lexical(Path(paths.input_ledger_path), project)
            != expected_input_ledger
            or _absolute_lexical(Path(paths.split_manifest_path), project)
            != expected_split_manifest
            or _absolute_lexical(
                Path(paths.non_lockbox_packet_path),
                project,
            )
            != expected_non_lockbox_packet
        ):
            raise RunnerError(
                "injected outputs must use fixed state-root paths"
            )
        if paths.public_material_root is None:
            raise RunnerError("injected public-material root is unavailable")
        try:
            _absolute_lexical(
                Path(paths.public_material_root), project
            ).relative_to(project)
        except ValueError as error:
            raise RunnerError(
                "injected public-material root must stay inside project root"
            ) from error
    else:
        raise RunnerError("runner path authority is invalid")
    if any(
        _contains_private_component(path)
        for path in (project, input_root, state_root, canonical_root)
    ):
        raise RunnerError("private path component is blocked")
    for label, candidate in (
        ("input root", input_root),
        ("state root", state_root),
        ("canonical root", canonical_root),
    ):
        try:
            candidate.relative_to(project)
        except ValueError as error:
            raise RunnerError(f"{label} must stay inside project root") from error
        _inspect_component_chain(candidate, trusted_root=project)
    if state_root == canonical_root:
        raise RunnerError("state and canonical roots must be distinct")
    try:
        canonical_root.relative_to(state_root)
    except ValueError:
        pass
    else:
        raise RunnerError("canonical root cannot be inside ignored state root")
    try:
        state_root.relative_to(canonical_root)
    except ValueError:
        pass
    else:
        raise RunnerError("ignored state root cannot be inside canonical root")


def _validate_input_path(paths: RunnerPaths, path: Path) -> Path:
    return _safe_path(
        path,
        allowed_root=paths.input_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )


def _read_verified_public_bytes(
    paths: RunnerPaths,
    path: Path,
    *,
    expected_sha256: str,
    expected_size_bytes: int,
    maximum_bytes: int,
) -> VerifiedMaterialBytes:
    _validate_layout(paths)
    if not isinstance(path, Path):
        raise RunnerError("public-material path must be a Path")
    if paths.public_material_root is None:
        raise RunnerError("public-material root is unavailable")
    expected_digest = _validate_digest(
        expected_sha256,
        "expected public-material digest",
    )
    if (
        type(expected_size_bytes) is not int
        or expected_size_bytes < 0
    ):
        raise RunnerError(
            "expected public-material size must be a non-negative integer"
        )
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise RunnerError(
            "maximum public-material size must be a non-negative integer"
        )
    if expected_size_bytes > maximum_bytes:
        raise RunnerError("expected public material exceeds the allowed size")

    public_root = _absolute_lexical(
        Path(paths.public_material_root),
        Path(paths.project_root),
    )
    validated_path = _safe_path(
        path,
        allowed_root=public_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    content = _read_file_nofollow(
        validated_path,
        maximum_bytes=maximum_bytes,
        require_single_link=True,
    )
    if type(content) is not bytes:
        raise RunnerError("bound public-material reader did not return bytes")
    actual_size = len(content)
    if actual_size > maximum_bytes:
        raise RunnerError("bound file exceeds the allowed size")
    actual_digest = _sha256_bytes(content)
    if actual_digest != expected_digest:
        raise RunnerError("public-material SHA-256 does not match expected")
    if actual_size != expected_size_bytes:
        raise RunnerError("public-material byte count does not match expected")
    logical_name = validated_path.relative_to(public_root).as_posix()
    return VerifiedMaterialBytes(
        logical_name=logical_name,
        content=content,
        sha256=actual_digest,
        size_bytes=actual_size,
    )


def _frozen_non_lockbox_public_source_reader(
    paths: RunnerPaths,
    sources: tuple[SourceByteIdentity, ...],
    *,
    family: Literal["crema_wav", "ami_xml"],
) -> Callable[[SourceByteIdentity], bytes]:
    """Mint one exact-set, byte-only source capability for the Cut 4 lane."""
    _validate_layout(paths)
    if (
        type(sources) is not tuple
        or not sources
        or type(family) is not str
        or family not in {"crema_wav", "ami_xml"}
    ):
        raise RunnerError("non-lockbox source authority is invalid")
    project_root = _absolute_lexical(
        Path(paths.project_root),
        Path(paths.project_root),
    )
    if paths.public_material_root is None:
        raise RunnerError("public-material root is unavailable")
    public_root = _absolute_lexical(
        Path(paths.public_material_root),
        project_root,
    )
    expected_family_root = _absolute_lexical(
        (
            Path(paths.crema_audio_root)
            if family == "crema_wav"
            else Path(paths.ami_extracted_root)
        ),
        project_root,
    )
    try:
        public_root.relative_to(project_root)
        expected_family_root.relative_to(public_root)
    except ValueError as error:
        raise RunnerError("non-lockbox source root is outside public material") from error

    frozen: dict[SourceByteIdentity, tuple[Path, str]] = {}
    for source in sources:
        if type(source) is not SourceByteIdentity:
            raise RunnerError("non-lockbox source identity type changed")
        relative_text = source.project_relative_path
        if (
            type(relative_text) is not str
            or not relative_text
            or "\\" in relative_text
        ):
            raise RunnerError("non-lockbox source path is not canonical")
        relative = Path(relative_text)
        if (
            relative.is_absolute()
            or relative.as_posix() != relative_text
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise RunnerError("non-lockbox source path is not canonical")
        candidate = _absolute_lexical(project_root / relative, project_root)
        try:
            candidate.relative_to(public_root)
        except ValueError as error:
            raise RunnerError(
                "non-lockbox source is outside fixed public material"
            ) from error
        if (
            _contains_private_component(candidate)
            or any(
                part.casefold() in REPOSITORY_METADATA_COMPONENTS
                for part in candidate.parts
            )
        ):
            raise RunnerError("non-lockbox source uses a blocked path component")
        if family == "crema_wav":
            if candidate.parent != expected_family_root or candidate.suffix != ".wav":
                raise RunnerError("CREMA source is outside the sealed WAV family")
        else:
            try:
                candidate.relative_to(expected_family_root)
            except ValueError as error:
                raise RunnerError("AMI source is outside the sealed XML family") from error
            if candidate.suffix != ".xml":
                raise RunnerError("AMI source is outside the sealed XML family")
        if type(source.sha256) is not str:
            raise RunnerError("non-lockbox source digest type changed")
        _validate_digest(source.sha256, "non-lockbox source")
        if type(source.size_bytes) is not int or source.size_bytes <= 0:
            raise RunnerError("non-lockbox source size is invalid")
        if source in frozen:
            raise RunnerError("non-lockbox source identity is duplicated")
        frozen[source] = (
            candidate,
            candidate.relative_to(public_root).as_posix(),
        )
    if len(frozen) != len(sources):  # pragma: no cover - guarded above
        raise RunnerError("non-lockbox source identity set changed")

    def read(source: SourceByteIdentity) -> bytes:
        if type(source) is not SourceByteIdentity or source not in frozen:
            raise RunnerError("unknown non-lockbox source identity")
        path, expected_logical_name = frozen[source]
        verified = _read_verified_public_bytes(
            paths,
            path,
            expected_sha256=source.sha256,
            expected_size_bytes=source.size_bytes,
            maximum_bytes=source.size_bytes,
        )
        if (
            type(verified) is not VerifiedMaterialBytes
            or type(verified.logical_name) is not str
            or verified.logical_name != expected_logical_name
            or type(verified.content) is not bytes
            or type(verified.sha256) is not str
            or verified.sha256 != source.sha256
            or type(verified.size_bytes) is not int
            or verified.size_bytes != source.size_bytes
            or len(verified.content) != source.size_bytes
            or _sha256_bytes(verified.content) != source.sha256
        ):
            raise RunnerError("non-lockbox source readback identity changed")
        return verified.content

    return read


def _validate_non_lockbox_path(paths: RunnerPaths) -> Path:
    try:
        return _safe_path(
            paths.non_lockbox_packet_path,
            allowed_root=paths.non_lockbox_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
    except RunnerError as error:
        raise RunnerError(f"non-lockbox artifact path rejected: {error}") from error


def _resolve_final_lockbox_result_path(paths: RunnerPaths) -> Path:
    if paths.authority == "production":
        if paths.lockbox_result_path is not None:
            raise RunnerError(
                "production lockbox-result capability must stay inert"
            )
        return Path(paths.state_root) / "lockbox" / "lockbox-result.json"
    if paths.authority == "injected-test":
        if paths.lockbox_result_path is None:
            raise RunnerError("injected lockbox-result path is unavailable")
        return Path(paths.lockbox_result_path)
    raise RunnerError("runner path authority is invalid")


def _validate_lockbox_path(paths: RunnerPaths) -> Path:
    try:
        return _safe_path(
            _resolve_final_lockbox_result_path(paths),
            allowed_root=paths.lockbox_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
    except RunnerError as error:
        raise RunnerError(f"lockbox artifact path rejected: {error}") from error


def _validate_canonical_pair_metadata(
    paths: RunnerPaths,
    *,
    require_entries: bool,
    allow_partial: bool = False,
) -> None:
    _validate_layout(paths)
    canonical_root = _safe_path(
        paths.canonical_root,
        allowed_root=paths.canonical_root,
        project_root=paths.project_root,
        final_kind="directory",
        require_final=False,
    )
    if os.path.lexists(canonical_root):
        try:
            entry_names = {entry.name for entry in canonical_root.iterdir()}
        except OSError as error:
            raise RunnerError("unable to inspect canonical directory") from error
        if not entry_names.issubset(
            {paths.result_path.name, paths.report_path.name}
        ):
            raise RunnerError(
                "canonical directory must contain exactly the result/report pair"
            )
    result_path = _safe_path(
        paths.result_path,
        allowed_root=paths.canonical_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=False,
    )
    report_path = _safe_path(
        paths.report_path,
        allowed_root=paths.canonical_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=False,
    )
    result_exists = os.path.lexists(result_path)
    report_exists = os.path.lexists(report_path)
    if result_exists != report_exists and not allow_partial:
        raise RunnerError("partial canonical pair")
    if require_entries and not (result_exists and report_exists):
        raise RunnerError("canonical pair is missing")
    for path, present in (
        (result_path, result_exists),
        (report_path, report_exists),
    ):
        if present:
            _safe_path(
                path,
                allowed_root=paths.canonical_root,
                project_root=paths.project_root,
                final_kind="file",
                require_final=True,
            )


def _sync_directory(
    path: Path,
    *,
    authority: _DirectoryAuthority | None = None,
) -> None:
    """Flush directory metadata.

    File-entry mutations pass the exact still-held parent authority. Pathname
    reopen is reserved for durable directory creation and is never used as the
    success barrier for create/replace/unlink.
    """
    directory = Path(path)
    if authority is not None:
        if directory != authority.path:
            raise RunnerError("directory barrier authority path does not match")
        if authority.posix_descriptor is not None:
            opened = os.fstat(authority.posix_descriptor)
            if not stat.S_ISDIR(opened.st_mode):
                raise RunnerError("POSIX barrier authority is not a directory")
            os.fsync(authority.posix_descriptor)
            return
        if authority.windows_handle is None:
            raise RunnerError("directory barrier authority handle is missing")
        from ctypes import wintypes

        flush = ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        ).FlushFileBuffers
        flush.argtypes = (wintypes.HANDLE,)
        flush.restype = wintypes.BOOL
        if not flush(authority.windows_handle):
            raise OSError(
                ctypes.get_last_error(),
                "unable to flush held directory barrier",
            )
        return

    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(directory, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return

    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    flush = kernel32.FlushFileBuffers
    flush.argtypes = (wintypes.HANDLE,)
    flush.restype = wintypes.BOOL
    close = kernel32.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    handle = create_file(
        str(directory),
        0x40000000,  # GENERIC_WRITE
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        3,  # OPEN_EXISTING
        0x02000000 | 0x00200000 | 0x80000000,
        None,
    )
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        raise OSError(ctypes.get_last_error(), "unable to open directory barrier")
    try:
        if not flush(handle):
            raise OSError(
                ctypes.get_last_error(),
                "unable to flush directory barrier",
            )
    finally:
        close(handle)


def _ensure_directory_durable(path: Path) -> None:
    missing: list[Path] = []
    cursor = Path(path)
    while not os.path.lexists(cursor):
        missing.append(cursor)
        parent = cursor.parent
        if parent == cursor:
            raise RunnerError("unable to find an existing directory ancestor")
        cursor = parent
    try:
        status = os.stat(cursor, follow_symlinks=False)
        if _is_link_or_reparse(cursor, status) or not stat.S_ISDIR(status.st_mode):
            raise RunnerError("directory ancestor is not a no-follow directory")
        for directory in reversed(missing):
            directory.mkdir()
            created = os.stat(directory, follow_symlinks=False)
            if _is_link_or_reparse(directory, created) or not stat.S_ISDIR(
                created.st_mode
            ):
                raise RunnerError("created directory identity is unsafe")
            _sync_directory(directory)
            _sync_directory(directory.parent)
    except OSError as error:
        raise RunnerError("unable to durably create directory") from error


def _windows_open_mutation_fd(
    path: Path,
    *,
    access: int,
    disposition: int,
    descriptor_flags: int,
    share_mode: int = 0x00000001 | 0x00000002,
) -> int:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        str(path),
        access,
        share_mode,
        None,
        disposition,
        0x00000080 | 0x00200000 | 0x80000000,
        None,
    )
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        raise OSError(ctypes.get_last_error(), "unable to open mutation handle")
    try:
        return msvcrt.open_osfhandle(handle, descriptor_flags)
    except Exception:
        kernel32.CloseHandle(handle)
        raise


def _verify_opened_mutation_identity(path: Path, descriptor: int) -> None:
    opened = os.fstat(descriptor)
    proof = _PATH_IDENTITY_PROOFS.get(str(Path(path)), ())
    expected = next(
        (
            (device, inode)
            for component, device, inode in proof
            if Path(component) == Path(path)
        ),
        None,
    )
    if expected is not None and (opened.st_dev, opened.st_ino) != expected:
        raise RunnerError("mutation target identity changed before handle open")
    inspected = os.stat(path, follow_symlinks=False)
    if (
        _is_link_or_reparse(path, inspected)
        or not stat.S_ISREG(opened.st_mode)
        or (opened.st_dev, opened.st_ino)
        != (inspected.st_dev, inspected.st_ino)
    ):
        raise RunnerError("mutation target handle identity does not match entry")


def _windows_unlink_by_handle(path: Path) -> None:
    from ctypes import wintypes

    descriptor = _windows_open_mutation_fd(
        path,
        access=0x00010000 | 0x00000080,  # DELETE | FILE_READ_ATTRIBUTES
        disposition=3,  # OPEN_EXISTING
        descriptor_flags=os.O_RDONLY | getattr(os, "O_BINARY", 0),
    )
    try:
        _verify_opened_mutation_identity(path, descriptor)
        handle = msvcrt.get_osfhandle(descriptor)

        class FileDispositionInfo(ctypes.Structure):
            _fields_ = (("DeleteFile", wintypes.BOOL),)

        information = FileDispositionInfo(True)
        set_information = ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        ).SetFileInformationByHandle
        set_information.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.LPVOID,
            wintypes.DWORD,
        )
        set_information.restype = wintypes.BOOL
        if not set_information(
            handle,
            4,  # FileDispositionInfo
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            raise OSError(
                ctypes.get_last_error(),
                "unable to mark file for handle-bound deletion",
            )
    finally:
        os.close(descriptor)


def _windows_rename_descriptor(
    descriptor: int,
    destination_name: str,
    *,
    destination_parent_handle: int,
) -> None:
    from ctypes import wintypes

    source_handle = msvcrt.get_osfhandle(descriptor)
    encoded_name = destination_name.encode("utf-16-le")

    class FileRenameInfoEx(ctypes.Structure):
        _fields_ = (
            ("Flags", wintypes.DWORD),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        )

    name_offset = FileRenameInfoEx.FileName.offset
    information_size = name_offset + len(encoded_name)
    buffer = ctypes.create_string_buffer(information_size)
    information = FileRenameInfoEx.from_buffer(buffer)
    information.Flags = 0  # exact-handle rename; never replace another entry
    information.RootDirectory = destination_parent_handle
    information.FileNameLength = len(encoded_name)
    ctypes.memmove(
        ctypes.addressof(buffer) + name_offset,
        encoded_name,
        len(encoded_name),
    )

    class IoStatusBlock(ctypes.Structure):
        _fields_ = (
            ("Status", ctypes.c_void_p),
            ("Information", ctypes.c_size_t),
        )

    io_status = IoStatusBlock()
    set_information = ctypes.WinDLL(
        "ntdll",
        use_last_error=True,
    ).NtSetInformationFile
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(IoStatusBlock),
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.c_int,
    )
    set_information.restype = ctypes.c_long
    status = set_information(
        source_handle,
        ctypes.byref(io_status),
        buffer,
        information_size,
        65,  # FileRenameInformationEx
    )
    if status != 0:
        raise OSError(
            status & 0xFFFFFFFF,
            "unable to perform exact-target handle-bound rename",
        )


def _windows_unlink_open_descriptor(descriptor: int) -> None:
    from ctypes import wintypes

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = (("DeleteFile", wintypes.BOOL),)

    information = FileDispositionInfo(True)
    set_information = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).SetFileInformationByHandle
    set_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    set_information.restype = wintypes.BOOL
    if not set_information(
        msvcrt.get_osfhandle(descriptor),
        4,  # FileDispositionInfo
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        raise OSError(
            ctypes.get_last_error(),
            "unable to mark held file for handle-bound deletion",
        )


def _windows_replace_by_handle(
    source: Path,
    destination: Path,
    *,
    source_descriptor: int,
    destination_descriptor: int | None,
    source_authority: _DirectoryAuthority,
    destination_authority: _DirectoryAuthority,
    prior_path: Path | None,
) -> None:
    _verify_opened_mutation_identity(source, source_descriptor)
    if source_authority.windows_handle is None:
        raise RunnerError("Windows source parent authority handle is missing")
    if destination_authority.windows_handle is None:
        raise RunnerError("Windows destination parent authority handle is missing")
    if destination_descriptor is not None:
        if prior_path is None:
            raise RunnerError("existing destination requires a preservation entry")
        _verify_opened_mutation_identity(destination, destination_descriptor)
        _windows_rename_descriptor(
            destination_descriptor,
            prior_path.name,
            destination_parent_handle=destination_authority.windows_handle,
        )
        _bind_mutated_entry(destination, present=False)
        _bind_mutated_entry(prior_path, present=True)
        _sync_directory(
            destination.parent,
            authority=destination_authority,
        )

    _windows_rename_descriptor(
        source_descriptor,
        destination.name,
        destination_parent_handle=destination_authority.windows_handle,
    )
    _bind_mutated_entry(source, present=False)
    _bind_mutated_entry(destination, present=True)
    _sync_directory(source.parent, authority=source_authority)
    if destination.parent != source.parent:
        _sync_directory(
            destination.parent,
            authority=destination_authority,
        )


def _write_new_fsynced(path: Path, content: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    _require_mutation_path_proof(path)
    try:
        with _trusted_parent_handles(
            path,
            include_target=False,
            mutation=True,
        ) as parent_authority:
            parent_descriptor = parent_authority.posix_descriptor
            _verify_cached_path_proof(path)
            if parent_descriptor is None:
                descriptor = _windows_open_mutation_fd(
                    path,
                    access=0x80000000 | 0x40000000,
                    disposition=1,  # CREATE_NEW
                    descriptor_flags=os.O_RDWR | getattr(os, "O_BINARY", 0),
                )
            else:
                descriptor = os.open(
                    path.name,
                    flags,
                    0o600,
                    dir_fd=parent_descriptor,
                )
            try:
                view = memoryview(content)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise OSError("short durable write")
                    view = view[written:]
                os.fsync(descriptor)
                opened = os.fstat(descriptor)
                if parent_descriptor is None:
                    inspected = os.stat(path, follow_symlinks=False)
                else:
                    inspected = os.stat(
                        path.name,
                        dir_fd=parent_descriptor,
                        follow_symlinks=False,
                    )
                if (
                    _is_link_or_reparse(path, inspected)
                    or (opened.st_dev, opened.st_ino)
                    != (inspected.st_dev, inspected.st_ino)
                ):
                    raise RunnerError("new file identity changed during create")
            finally:
                os.close(descriptor)
            _bind_mutated_entry(path, present=True)
            _sync_directory(path.parent, authority=parent_authority)
    except OSError as error:
        raise RunnerError(f"unable to durably write {path.name}") from error


def _replacement_control_paths(destination: Path) -> tuple[Path, Path]:
    destination = Path(destination)
    token = hashlib.sha256(destination.name.encode("utf-8")).hexdigest()[:32]
    stem = f".phase-b-replace-{token}"
    return (
        destination.parent / f"{stem}.intent.json",
        destination.parent / f"{stem}.prior",
    )


def _validate_replacement_intent(
    payload: Any,
    *,
    destination: Path,
    prior_path: Path,
) -> dict[str, Any]:
    expected = {
        "schema_version",
        "destination_name",
        "prior_name",
        "source_sha256",
        "prior_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise RunnerError("invalid durable replacement intent fields")
    if (
        type(payload["schema_version"]) is not int
        or payload["schema_version"] != _REPLACE_INTENT_SCHEMA_VERSION
    ):
        raise RunnerError("invalid durable replacement intent schema")
    if payload["destination_name"] != destination.name:
        raise RunnerError("durable replacement intent destination mismatch")
    if payload["prior_name"] != prior_path.name:
        raise RunnerError("durable replacement intent prior mismatch")
    _validate_digest(payload["source_sha256"], "replacement source")
    _validate_digest(payload["prior_sha256"], "replacement prior")
    return dict(payload)


def _recover_windows_replacement(destination: Path) -> str:
    """Resolve a durable exact-target preservation intent after interruption."""
    if os.name != "nt":
        return "none"
    destination = Path(destination)
    _require_mutation_path_proof(destination)
    intent_path, prior_path = _replacement_control_paths(destination)
    _seed_sibling_path_proof(destination, intent_path)
    _seed_sibling_path_proof(destination, prior_path)
    intent_exists = os.path.lexists(intent_path)
    prior_exists = os.path.lexists(prior_path)
    if not intent_exists:
        if prior_exists:
            raise RunnerError(
                "orphaned durable replacement prior is retained for review"
            )
        return "none"

    intent = _validate_replacement_intent(
        _load_json_object(intent_path, "durable replacement intent"),
        destination=destination,
        prior_path=prior_path,
    )
    destination_exists = os.path.lexists(destination)
    destination_descriptor: int | None = None
    destination_digest: str | None = None
    if destination_exists:
        try:
            destination_descriptor = _windows_open_mutation_fd(
                destination,
                access=0x80000000 | 0x00000080,
                disposition=3,
                descriptor_flags=os.O_RDONLY | getattr(os, "O_BINARY", 0),
                share_mode=0x00000001,  # exclude write and delete sharing
            )
            _verify_opened_mutation_identity(
                destination,
                destination_descriptor,
            )
            destination_digest = _sha256_descriptor(destination_descriptor)
        except (OSError, RunnerError) as error:
            if destination_descriptor is not None:
                os.close(destination_descriptor)
            raise RunnerError(
                "unable to hold exact recovery destination; evidence retained"
            ) from error

    def verify_held_destination(expected_digest: str) -> None:
        if (
            destination_descriptor is None
            or _sha256_descriptor(destination_descriptor) != expected_digest
        ):
            raise RunnerError(
                "held recovery destination changed; evidence retained"
            )

    try:
        if prior_exists:
            if _sha256_file(prior_path) != intent["prior_sha256"]:
                raise RunnerError(
                    "durable replacement prior digest mismatch; evidence retained"
                )
            if destination_exists:
                if destination_digest != intent["source_sha256"]:
                    raise RunnerError(
                        "durable replacement destination conflicts; evidence retained"
                    )
                verify_held_destination(intent["source_sha256"])
                _durable_unlink(prior_path, missing_ok=False)
                verify_held_destination(intent["source_sha256"])
                _durable_unlink(intent_path, missing_ok=False)
                verify_held_destination(intent["source_sha256"])
                return "committed"

            with _trusted_parent_handles(
                prior_path,
                include_target=False,
                mutation=True,
            ) as parent_authority:
                if parent_authority.windows_handle is None:
                    raise RunnerError(
                        "Windows replacement recovery authority is missing"
                    )
                descriptor = _windows_open_mutation_fd(
                    prior_path,
                    access=0x80000000 | 0x00010000 | 0x00000080,
                    disposition=3,
                    descriptor_flags=os.O_RDONLY | getattr(os, "O_BINARY", 0),
                )
                try:
                    _verify_opened_mutation_identity(prior_path, descriptor)
                    _windows_rename_descriptor(
                        descriptor,
                        destination.name,
                        destination_parent_handle=parent_authority.windows_handle,
                    )
                    _bind_mutated_entry(prior_path, present=False)
                    _bind_mutated_entry(destination, present=True)
                    _sync_directory(
                        destination.parent,
                        authority=parent_authority,
                    )
                finally:
                    os.close(descriptor)
            if _sha256_file(destination) != intent["prior_sha256"]:
                raise RunnerError(
                    "restored durable replacement prior digest mismatch"
                )
            _durable_unlink(intent_path, missing_ok=False)
            return "restored"

        if destination_digest not in {
            intent["prior_sha256"],
            intent["source_sha256"],
        }:
            raise RunnerError(
                "durable replacement state is ambiguous; evidence retained"
            )
        outcome = (
            "committed"
            if destination_digest == intent["source_sha256"]
            else "not_started"
        )
        verify_held_destination(destination_digest)
        _durable_unlink(intent_path, missing_ok=False)
        verify_held_destination(destination_digest)
        return outcome
    finally:
        if destination_descriptor is not None:
            os.close(destination_descriptor)


def _recover_output_replacement(
    paths: RunnerPaths,
    path: Path,
    *,
    allowed_root: Path,
) -> str:
    target = _safe_path(
        path,
        allowed_root=allowed_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=False,
    )
    outcome = _recover_windows_replacement(target)
    if os.path.lexists(target):
        _safe_path(
            target,
            allowed_root=allowed_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
    return outcome


def _replace_entry_durably(source: Path, destination: Path) -> None:
    if os.name != "nt":
        raise RunnerError(
            "POSIX existing-destination replacement is not qualified; "
            "Phase B file replacement fails closed on this platform"
        )
    _require_mutation_path_proof(source)
    _require_mutation_path_proof(destination)
    _recover_windows_replacement(destination)
    source_parent = os.stat(source.parent, follow_symlinks=False)
    destination_parent = os.stat(destination.parent, follow_symlinks=False)
    if source_parent.st_dev != destination_parent.st_dev:
        raise RunnerError("atomic replace roots are on different devices")
    try:
        with _trusted_parent_handles(
            source,
            include_target=False,
            mutation=True,
        ) as source_authority, _trusted_parent_handles(
            destination,
            include_target=False,
            mutation=True,
        ) as destination_authority:
            _verify_cached_path_proof(source)
            _verify_cached_path_proof(destination)
            if (
                source_authority.windows_handle is None
                or destination_authority.windows_handle is None
            ):
                raise RunnerError("Windows replace authority handle is missing")
            source_descriptor = _windows_open_mutation_fd(
                source,
                access=0x80000000 | 0x00010000 | 0x00000080,
                disposition=3,
                descriptor_flags=os.O_RDONLY | getattr(os, "O_BINARY", 0),
            )
            destination_descriptor: int | None = None
            intent_path: Path | None = None
            prior_path: Path | None = None
            try:
                _verify_opened_mutation_identity(source, source_descriptor)
                if os.path.lexists(destination):
                    intent_path, prior_path = _replacement_control_paths(
                        destination
                    )
                    _seed_sibling_path_proof(destination, intent_path)
                    _seed_sibling_path_proof(destination, prior_path)
                    if os.path.lexists(intent_path) or os.path.lexists(prior_path):
                        raise RunnerError(
                            "durable replacement control entry already exists"
                        )
                    destination_descriptor = _windows_open_mutation_fd(
                        destination,
                        access=0x80000000 | 0x00010000 | 0x00000080,
                        disposition=3,
                        descriptor_flags=(
                            os.O_RDONLY | getattr(os, "O_BINARY", 0)
                        ),
                    )
                    _verify_opened_mutation_identity(
                        destination,
                        destination_descriptor,
                    )
                    intent = {
                        "schema_version": _REPLACE_INTENT_SCHEMA_VERSION,
                        "destination_name": destination.name,
                        "prior_name": prior_path.name,
                        "source_sha256": _sha256_descriptor(source_descriptor),
                        "prior_sha256": _sha256_descriptor(
                            destination_descriptor
                        ),
                    }
                    _write_new_fsynced(
                        intent_path,
                        canonical_json_bytes(intent),
                    )
                _windows_replace_by_handle(
                    source,
                    destination,
                    source_descriptor=source_descriptor,
                    destination_descriptor=destination_descriptor,
                    source_authority=source_authority,
                    destination_authority=destination_authority,
                    prior_path=prior_path,
                )
                if destination_descriptor is not None:
                    if prior_path is None or intent_path is None:
                        raise RunnerError(
                            "durable replacement cleanup state is incomplete"
                        )
                    _windows_unlink_open_descriptor(destination_descriptor)
                    os.close(destination_descriptor)
                    destination_descriptor = None
                    _bind_mutated_entry(prior_path, present=False)
                    _sync_directory(
                        destination.parent,
                        authority=destination_authority,
                    )
                    _durable_unlink(intent_path, missing_ok=False)
            finally:
                if destination_descriptor is not None:
                    os.close(destination_descriptor)
                os.close(source_descriptor)
    except OSError as error:
        raise RunnerError("exact-target durable replacement failed") from error


def _durable_unlink(path: Path, *, missing_ok: bool = True) -> None:
    if missing_ok and not os.path.lexists(path):
        target = Path(path)
        proof = _PATH_IDENTITY_PROOFS.get(str(target))
        if proof is not None:
            _PATH_IDENTITY_PROOFS[str(target)] = tuple(
                item for item in proof if Path(item[0]) != target
            )
        _require_mutation_path_proof(target)
        return
    _require_mutation_path_proof(path)
    try:
        with _trusted_parent_handles(
            path,
            include_target=False,
            mutation=True,
        ) as parent_authority:
            parent_descriptor = parent_authority.posix_descriptor
            _verify_cached_path_proof(path)
            if parent_descriptor is None:
                _windows_unlink_by_handle(path)
            else:
                os.unlink(path.name, dir_fd=parent_descriptor)
            _bind_mutated_entry(path, present=False)
            _sync_directory(path.parent, authority=parent_authority)
    except FileNotFoundError:
        if not missing_ok:
            raise
        return
    except OSError as error:
        raise RunnerError(f"unable to durably remove {path.name}") from error


def _replace_bytes_durably(path: Path, content: bytes) -> None:
    _ensure_directory_durable(path.parent)
    _require_mutation_path_proof(path)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    _PATH_IDENTITY_PROOFS[str(temporary)] = tuple(
        item
        for item in _PATH_IDENTITY_PROOFS[str(Path(path))]
        if Path(item[0]) != Path(path)
    )
    try:
        _write_new_fsynced(temporary, content)
        _replace_entry_durably(temporary, path)
    except Exception:
        try:
            _durable_unlink(temporary)
        except (OSError, RunnerError):
            pass
        raise


def _initial_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "phase": "initialized",
        "configuration_sha256": "",
        "environment_lock_sha256": "",
        "input_ledger_sha256": "",
        "split_manifest_sha256": "",
        "non_lockbox_packet_sha256": "",
        "lockbox_open_count": 0,
        "lockbox_result_sha256": "",
        "lockbox_decision_evidence_sha256": "",
        "lockbox_decision_evidence_mint_sha256": "",
        "candidate_transaction_id": "",
    }


def _validate_state(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != STATE_FIELDS:
        raise RunnerError("invalid Phase B state fields")
    if (
        type(payload["schema_version"]) is not int
        or payload["schema_version"] != STATE_SCHEMA_VERSION
    ):
        raise RunnerError("invalid Phase B state schema version")
    phase = payload["phase"]
    if not isinstance(phase, str) or phase not in ALLOWED_PHASES:
        raise RunnerError("invalid Phase B state phase")
    if phase == "initialized":
        if any(payload[field] != "" for field in DIGEST_FIELDS):
            raise RunnerError("initialized state digest fields must be empty")
    else:
        for field in DIGEST_FIELDS:
            _validate_digest(payload[field], field)
        for field in (
            "configuration_sha256",
            "environment_lock_sha256",
            "input_ledger_sha256",
            "split_manifest_sha256",
        ):
            if payload[field] == UNSET_DIGEST:
                raise RunnerError(f"{phase} state has an unset anchor digest")
        if phase == "preflight_complete":
            if (
                payload["non_lockbox_packet_sha256"] != UNSET_DIGEST
                or payload["lockbox_result_sha256"] != UNSET_DIGEST
                or payload["lockbox_decision_evidence_sha256"] != UNSET_DIGEST
                or payload["lockbox_decision_evidence_mint_sha256"]
                != UNSET_DIGEST
            ):
                raise RunnerError(
                    "preflight state must retain unopened artifact placeholders"
                )
        elif phase == "non_lockbox_complete":
            if (
                payload["non_lockbox_packet_sha256"] == UNSET_DIGEST
                or payload["lockbox_result_sha256"] != UNSET_DIGEST
                or payload["lockbox_decision_evidence_sha256"] != UNSET_DIGEST
                or payload["lockbox_decision_evidence_mint_sha256"]
                != UNSET_DIGEST
            ):
                raise RunnerError(
                    "non-lockbox state artifact digests do not match its phase"
                )
        elif (
            payload["non_lockbox_packet_sha256"] == UNSET_DIGEST
            or payload["lockbox_result_sha256"] == UNSET_DIGEST
            or payload["lockbox_decision_evidence_sha256"] == UNSET_DIGEST
            or payload["lockbox_decision_evidence_mint_sha256"]
            == UNSET_DIGEST
        ):
            raise RunnerError(f"{phase} state has an unset artifact digest")
    open_count = payload["lockbox_open_count"]
    if type(open_count) is not int or open_count not in (0, 1):
        raise RunnerError("invalid lockbox open count")
    lockbox_opened = phase in {
        "lockbox_complete",
        "awaiting_acceptance",
        "accepted",
        "rejected",
    }
    if open_count != (1 if lockbox_opened else 0):
        raise RunnerError("lockbox open count does not match state phase")
    transaction_id = payload["candidate_transaction_id"]
    transaction_phase = phase in {"awaiting_acceptance", "accepted", "rejected"}
    if transaction_phase:
        _validate_transaction_id(transaction_id)
    elif transaction_id != "":
        raise RunnerError("state records a transaction before publication")
    return dict(payload)


def _load_json_object_bytes(content: bytes, label: str) -> dict[str, Any]:
    try:
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"duplicate JSON key: {key}")
                value[key] = item
            return value

        payload = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {value}")
            ),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise RunnerError(f"invalid {label}: {error}") from error
    if not isinstance(payload, dict):
        raise RunnerError(f"{label} must be a JSON object")
    return payload


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    return _load_json_object_bytes(_read_file_nofollow(path), label)


def load_state(
    paths: RunnerPaths,
    *,
    recover: bool = True,
) -> dict[str, Any]:
    _validate_layout(paths)
    state_path = _safe_path(
        paths.state_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=False,
    )
    if recover:
        _recover_windows_replacement(state_path)
    state_path = _safe_path(
        state_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    return _validate_state(_load_json_object(state_path, "Phase B state"))


def _write_state(paths: RunnerPaths, state: Mapping[str, Any]) -> dict[str, Any]:
    validated = _validate_state(dict(state))
    _safe_path(
        paths.state_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
    )
    _replace_bytes_durably(paths.state_path, canonical_json_bytes(validated))
    readback = load_state(paths)
    if readback != validated:
        raise RunnerError("Phase B state readback mismatch")
    return readback


def initialize_state(paths: RunnerPaths) -> dict[str, Any]:
    _validate_layout(paths)
    if os.path.lexists(paths.state_path):
        return load_state(paths)
    _ensure_directory_durable(Path(paths.state_root))
    return _write_state(paths, _initial_state())


def _require_phase(state: Mapping[str, Any], expected: str) -> None:
    if state["phase"] != expected:
        raise RunnerError(
            f"invalid state transition from {state['phase']}; expected {expected}"
        )


def _transition(
    paths: RunnerPaths,
    state: Mapping[str, Any],
    target: str,
    **changes: Any,
) -> dict[str, Any]:
    current = state["phase"]
    allowed = ALLOWED_TRANSITIONS.get(current)
    valid = target in allowed if isinstance(allowed, frozenset) else target == allowed
    if not valid:
        raise RunnerError(f"invalid state transition: {current} -> {target}")
    updated = dict(state)
    updated.update(changes)
    updated["phase"] = target
    return _write_state(paths, updated)


def _forbidden_credentials() -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name, value in os.environ.items()
            if value
            and (
                name.upper() in CREDENTIAL_ENV_NAMES
                or name.upper().endswith(CREDENTIAL_ENV_SUFFIXES)
            )
        )
    )


def _forbidden_network_configuration() -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name, value in os.environ.items()
            if value
            and (
                name.upper() in NETWORK_CONFIGURATION_ENV_NAMES
                or name.upper().endswith(
                    NETWORK_CONFIGURATION_ENV_SUFFIXES
                )
            )
        )
    )


def _assert_closed_environment() -> None:
    credentials = _forbidden_credentials()
    if credentials:
        raise RunnerError(
            "credential environment variables are blocked: "
            + ", ".join(credentials)
        )
    network_configuration = _forbidden_network_configuration()
    if network_configuration:
        raise RunnerError(
            "network/configuration environment variables are blocked: "
            + ", ".join(network_configuration)
        )
    forbidden_modules = tuple(
        sorted(
            name
            for name in sys.modules
            if any(
                name == prefix or name.startswith(prefix + ".")
                for prefix in FORBIDDEN_RUNTIME_PREFIXES
            )
        )
    )
    if forbidden_modules:
        raise RunnerError(
            "runtime imports are blocked: " + ", ".join(forbidden_modules)
        )


_STATIC_PREFLIGHT_FIELDS = (
    ("configuration", "configuration_sha256"),
    ("environment lock", "environment_lock_sha256"),
    ("feature schema", "feature_schema_sha256"),
    ("split schema", "split_schema_sha256"),
)


def _static_preflight_paths(paths: RunnerPaths) -> tuple[Path, ...]:
    return (
        Path(paths.config_path),
        Path(paths.environment_lock_path),
        Path(paths.feature_schema_path),
        Path(paths.split_schema_path),
    )


def _validate_static_preflight_bytes(
    contents: tuple[bytes, ...],
) -> dict[str, Any]:
    if len(contents) != 4 or any(type(content) is not bytes for content in contents):
        raise RunnerError("tracked static byte shape changed")
    payloads: list[dict[str, Any]] = []
    for content, (label, digest_field) in zip(
        contents,
        _STATIC_PREFLIGHT_FIELDS,
        strict=True,
    ):
        if _sha256_bytes(content) != EXPECTED_STATIC_FILE_SHA256[digest_field]:
            raise RunnerError(f"{label} tracked bytes do not match the frozen identity")
        payloads.append(_load_json_object_bytes(content, label))
    try:
        configuration = validate_config(payloads[0])
        validate_environment_lock(payloads[1])
        feature_schema = validate_feature_schema(payloads[2])
        validate_split_schema(payloads[3])
        configuration, _ = validate_config_feature_schema_binding(
            configuration,
            feature_schema,
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"preflight static validation failed: {error}") from error
    return configuration


def _revalidate_held_static_preflight_inputs(
    authority: _HeldStaticPreflightInputs,
) -> None:
    if type(authority) is not _HeldStaticPreflightInputs:
        raise RunnerError("held static-input authority type changed")
    for file in authority.files:
        _verify_held_regular_file_metadata(file)
    current = tuple(
        _read_held_regular_file_bytes(file) for file in authority.files
    )
    if current != authority.contents or tuple(
        _sha256_bytes(content) for content in current
    ) != authority.digests:
        raise RunnerError("tracked static input changed through its held handle")
    if _validate_static_preflight_bytes(current) != authority.configuration:
        raise RunnerError("tracked static semantics changed")


@contextmanager
def _held_preflight_static_inputs(
    paths: RunnerPaths,
) -> Iterator[_HeldStaticPreflightInputs]:
    validated_paths = tuple(
        _validate_input_path(paths, path)
        for path in _static_preflight_paths(paths)
    )
    with ExitStack() as stack:
        opened = tuple(
            stack.enter_context(
                _held_regular_file_with_bytes(path, proof_bound=True)
            )
            for path in validated_paths
        )
        files = tuple(authority for authority, _content in opened)
        contents = tuple(content for _authority, content in opened)
        configuration = _validate_static_preflight_bytes(contents)
        authority = _HeldStaticPreflightInputs(
            configuration=configuration,
            contents=contents,
            digests=tuple(_sha256_bytes(content) for content in contents),
            files=files,
        )
        yield authority
        _revalidate_held_static_preflight_inputs(authority)


def _environment_wheel_filenames() -> tuple[str, ...]:
    distributions = EXPECTED_ENVIRONMENT_LOCK.get("distributions")
    if type(distributions) is not list or len(distributions) != 5:
        raise RunnerError("frozen environment distribution set changed")
    filenames = tuple(
        distribution.get("wheel_filename")
        if type(distribution) is dict
        else None
        for distribution in distributions
    )
    if (
        any(
            type(filename) is not str
            or not filename
            or Path(filename).name != filename
            for filename in filenames
        )
        or len(set(filenames)) != len(filenames)
    ):
        raise RunnerError("frozen environment wheel filename set changed")
    return filenames  # type: ignore[return-value]


def _revalidate_held_environment_wheel_inputs(
    authority: _HeldEnvironmentWheelInputs,
) -> None:
    if type(authority) is not _HeldEnvironmentWheelInputs:
        raise RunnerError("held environment-wheel authority type changed")
    expected_names = _environment_wheel_filenames()
    if (
        authority.filenames != expected_names
        or len(authority.files) != len(expected_names)
        or tuple(file.path.name for file in authority.files) != expected_names
    ):
        raise RunnerError("held environment-wheel order changed")
    for file in authority.files:
        _verify_held_regular_file_metadata(file)
    current = tuple(
        _read_held_regular_file_bytes(file) for file in authority.files
    )
    if (
        current != authority.contents
        or tuple(_sha256_bytes(content) for content in current)
        != authority.digests
    ):
        raise RunnerError("held environment-wheel bytes changed")


@contextmanager
def _held_environment_wheel_inputs(
    paths: RunnerPaths,
) -> Iterator[_HeldEnvironmentWheelInputs]:
    filenames = _environment_wheel_filenames()
    wheelhouse = _absolute_lexical(
        Path(paths.project_root)
        / ".tmp"
        / "emotion-state-002-phase-b"
        / "dependencies"
        / "wheelhouse",
        Path(paths.project_root),
    )
    with ExitStack() as stack:
        opened = tuple(
            stack.enter_context(_held_regular_file_with_bytes(
                _safe_path(
                    wheelhouse / filename,
                    allowed_root=wheelhouse,
                    project_root=paths.project_root,
                    final_kind="file",
                    require_final=True,
                ),
                maximum_bytes=1_073_741_824,
                proof_bound=True,
            ))
            for filename in filenames
        )
        files = tuple(file for file, _content in opened)
        contents = tuple(content for _file, content in opened)
        authority = _HeldEnvironmentWheelInputs(
            filenames=filenames,
            contents=contents,
            digests=tuple(_sha256_bytes(content) for content in contents),
            files=files,
        )
        _revalidate_held_environment_wheel_inputs(authority)
        yield authority
        _revalidate_held_environment_wheel_inputs(authority)


def _revalidate_held_tracked_public_evidence_inputs(
    authority: _HeldTrackedPublicEvidenceInputs,
) -> None:
    if type(authority) is not _HeldTrackedPublicEvidenceInputs:
        raise RunnerError("held tracked-evidence authority type changed")
    expected_names = tuple(TRACKED_DATASET_EVIDENCE_FILENAMES)
    if (
        len(expected_names) != 6
        or authority.names != expected_names
        or len(authority.files) != len(expected_names)
        or tuple(file.path.name for file in authority.files) != expected_names
    ):
        raise RunnerError("held tracked-evidence order changed")
    for file in authority.files:
        _verify_held_regular_file_metadata(file)
    current = tuple(
        _read_held_regular_file_bytes(file) for file in authority.files
    )
    if (
        current != authority.contents
        or tuple(_sha256_bytes(content) for content in current)
        != authority.digests
    ):
        raise RunnerError("held tracked-evidence bytes changed")


@contextmanager
def _held_tracked_public_evidence_inputs(
    paths: RunnerPaths,
) -> Iterator[_HeldTrackedPublicEvidenceInputs]:
    names = tuple(TRACKED_DATASET_EVIDENCE_FILENAMES)
    if len(names) != 6 or len(set(names)) != len(names):
        raise RunnerError("frozen tracked-evidence filename set changed")
    evidence_root = _absolute_lexical(
        Path(paths.dataset_evidence_root),
        Path(paths.project_root),
    )
    with ExitStack() as stack:
        opened = tuple(
            stack.enter_context(_held_regular_file_with_bytes(
                _safe_path(
                    evidence_root / name,
                    allowed_root=evidence_root,
                    project_root=paths.project_root,
                    final_kind="file",
                    require_final=True,
                ),
                proof_bound=True,
            ))
            for name in names
        )
        files = tuple(file for file, _content in opened)
        contents = tuple(content for _file, content in opened)
        authority = _HeldTrackedPublicEvidenceInputs(
            names=names,
            contents=contents,
            digests=tuple(_sha256_bytes(content) for content in contents),
            files=files,
        )
        _revalidate_held_tracked_public_evidence_inputs(authority)
        yield authority
        _revalidate_held_tracked_public_evidence_inputs(authority)


def _tracked_public_authority_from_held_evidence(
    evidence: _HeldTrackedPublicEvidenceInputs,
) -> tuple[TrackedPublicAuthority, str]:
    _revalidate_held_tracked_public_evidence_inputs(evidence)
    snapshot = dict(zip(evidence.names, evidence.contents, strict=True))
    try:
        authority = validate_tracked_public_evidence(dict(snapshot))
        commitment = tracked_public_authority_commitment_sha256(
            tracked_evidence=dict(snapshot),
            authority=authority,
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"held tracked public evidence is invalid: {error}") from error
    if type(authority) is not TrackedPublicAuthority:
        raise RunnerError("held tracked public authority type changed")
    _validate_digest(commitment, "tracked public authority commitment")
    _revalidate_held_tracked_public_evidence_inputs(evidence)
    return authority, commitment


def _read_tracked_preflight_evidence(
    paths: RunnerPaths,
) -> tuple[dict[str, bytes], tuple[tuple[str, bytes], ...]]:
    snapshot: dict[str, bytes] = {}
    pairs: list[tuple[str, bytes]] = []
    for name in TRACKED_DATASET_EVIDENCE_FILENAMES:
        path = _safe_path(
            paths.dataset_evidence_root / name,
            allowed_root=paths.dataset_evidence_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
        content = _read_file_nofollow(path)
        if type(content) is not bytes:
            raise RunnerError("tracked evidence reader did not return exact bytes")
        snapshot[name] = content
        pairs.append((name, content))
    return snapshot, tuple(pairs)


def _crosscheck_built_preflight_artifacts(
    artifacts: ProductionPreflightArtifacts,
    *,
    authority: TrackedPublicAuthority,
    finished_responses: bytes,
    summary_table: bytes,
) -> None:
    finished_digest = _sha256_bytes(finished_responses)
    summary_digest = _sha256_bytes(summary_table)
    ledger = artifacts.input_ledger
    raw = ledger.get("raw_csv_sha256")
    source = ledger.get("crema_label_ledger", {}).get("source_binding")
    if raw != {
        "finishedResponses.csv": finished_digest,
        "processedResults/summaryTable.csv": summary_digest,
    } or not isinstance(source, dict) or (
        source.get("finished_responses_sha256") != finished_digest
        or source.get("summary_table_sha256") != summary_digest
    ):
        raise RunnerError("preflight ledger CSV source binding changed")
    if (
        finished_digest != authority.crema_finished_responses.sha256
        or len(finished_responses) != authority.crema_finished_responses.size_bytes
        or summary_digest != authority.crema_summary_table.sha256
        or len(summary_table) != authority.crema_summary_table.size_bytes
    ):
        raise RunnerError("preflight CSV authority cross-check failed")
    acoustic_by_stem: dict[str, tuple[str, int]] = {}
    for identity in authority.crema_audio:
        path = identity.project_relative_path
        if not path.endswith(".wav"):
            raise RunnerError("CREMA acoustic authority path changed")
        stem = path.rsplit("/", 1)[-1][:-4]
        if not stem or stem in acoustic_by_stem:
            raise RunnerError("CREMA acoustic authority stem changed")
        acoustic_by_stem[stem] = (identity.sha256, identity.size_bytes)
    for role in NONFINAL_PARTITION_ROLES:
        cache = artifacts.partition_authority_caches[role]
        for record in cache["records"]:
            if acoustic_by_stem.get(record["clip_stem"]) != (
                record["audio_sha256"],
                record["audio_size_bytes"],
            ):
                raise RunnerError("preflight cache acoustic authority changed")


def _compare_restored_preflight_authority(
    artifacts: ProductionPreflightArtifacts,
    restored: Mapping[str, Any],
) -> None:
    from scripts import emotion_state_phase_b_evaluation as evaluation

    for role in NONFINAL_PARTITION_ROLES:
        expected = evaluation.restore_validated_partition_authority_cache(
            artifacts.partition_authority_caches[role],
            artifacts.split_manifest,
            role=role,
        )
        actual = restored[role]
        if (
            actual.to_payload() != expected.to_payload()
            or evaluation.validated_partition_records(actual, role=role)
            != evaluation.validated_partition_records(expected, role=role)
        ):
            raise RunnerError("persisted partition restoration changed")


@contextmanager
def _classify_post_commit_unwind(
    marker: list[bool],
    *,
    boundary: Literal["build", "outer"],
) -> Iterator[None]:
    try:
        yield
    except Exception as error:
        if marker == [True]:
            if isinstance(error, RunnerError) and "indeterminate" in str(error):
                raise
            label = (
                "post-commit build unwind"
                if boundary == "build"
                else "post-commit outer unwind"
            )
            raise RunnerError(
                f"preflight state outcome is indeterminate during {label}: {error}"
            ) from error
        raise


def _run_admitted_preflight_build(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
    state_authority: _AdmittedStateAuthority,
) -> dict[str, Any]:
    committed_yielded = [False]
    with _classify_post_commit_unwind(committed_yielded, boundary="build"):
        with _held_preflight_static_inputs(paths) as static_authority:
            configuration = static_authority.configuration
            static_digests = {
                field: digest
                for (_label, field), digest in zip(
                    _STATIC_PREFLIGHT_FIELDS,
                    static_authority.digests,
                    strict=True,
                )
            }
            evidence, evidence_pairs = _read_tracked_preflight_evidence(paths)
            try:
                early_authority = validate_tracked_public_evidence(dict(evidence_pairs))
                early_commitment = tracked_public_authority_commitment_sha256(
                    tracked_evidence=dict(evidence_pairs),
                    authority=early_authority,
                )
            except (TypeError, ValueError) as error:
                raise RunnerError(f"tracked public evidence is invalid: {error}") from error

            finished = _read_verified_public_bytes(
                paths,
                paths.crema_finished_responses_path,
                expected_sha256=early_authority.crema_finished_responses.sha256,
                expected_size_bytes=early_authority.crema_finished_responses.size_bytes,
                maximum_bytes=early_authority.crema_finished_responses.size_bytes,
            ).content
            summary = _read_verified_public_bytes(
                paths,
                paths.crema_summary_table_path,
                expected_sha256=early_authority.crema_summary_table.sha256,
                expected_size_bytes=early_authority.crema_summary_table.size_bytes,
                maximum_bytes=early_authority.crema_summary_table.size_bytes,
            ).content
            try:
                artifacts = build_production_preflight_artifacts(
                    tracked_evidence=dict(evidence_pairs),
                    finished_responses=finished,
                    summary_table=summary,
                    configuration=deepcopy(configuration),
                )
            except (TypeError, ValueError) as error:
                raise RunnerError(f"production preflight build failed: {error}") from error
            if artifacts.source_authority_commitment_sha256 != early_commitment:
                raise RunnerError("early and builder source authorities differ")
            _crosscheck_built_preflight_artifacts(
                artifacts,
                authority=early_authority,
                finished_responses=finished,
                summary_table=summary,
            )

            with _held_preflight_output_authorities(
                paths,
                material_authority,
            ) as output_authorities, _persist_preflight_artifacts(
                paths,
                artifacts,
                material_authority=material_authority,
                output_authorities=output_authorities,
            ) as readback:
                manifest_file_sha256 = readback.files[1].sha256
                restored = {
                    role: _load_bound_partition_authority(
                        paths,
                        role=role,
                        expected_split_manifest_file_sha256=manifest_file_sha256,
                        material_authority=material_authority,
                        output_authorities=output_authorities,
                        readback_authority=readback,
                    )
                    for role in NONFINAL_PARTITION_ROLES
                }
                _compare_restored_preflight_authority(artifacts, restored)
                _assert_closed_environment()
                _revalidate_held_static_preflight_inputs(static_authority)
                _verify_material_pipeline_authority(material_authority)
                _verify_admitted_state_cas(
                    paths,
                    state_authority,
                    state_root=material_authority.state_root,
                )
                _validate_preflight_output_shape(
                    paths,
                    output_authorities,
                    require_complete=True,
                    allow_controls=False,
                )
                for authority in readback.files:
                    _verify_held_regular_file_authority(authority)
                _validate_state_root_allowlist(
                    paths,
                    material_authority.state_root,
                    allow_state_controls=False,
                )
                proposed = _initial_state()
                proposed.update(
                    {
                        "phase": "preflight_complete",
                        "configuration_sha256": static_digests["configuration_sha256"],
                        "environment_lock_sha256": static_digests["environment_lock_sha256"],
                        "input_ledger_sha256": readback.files[0].sha256,
                        "split_manifest_sha256": readback.files[1].sha256,
                        "non_lockbox_packet_sha256": UNSET_DIGEST,
                        "lockbox_result_sha256": UNSET_DIGEST,
                        "lockbox_decision_evidence_sha256": UNSET_DIGEST,
                        "lockbox_decision_evidence_mint_sha256": UNSET_DIGEST,
                    }
                )
                proposed = _validate_state(proposed)
                with _commit_preflight_state_durably(
                    paths,
                    proposed,
                    material_authority=material_authority,
                    admitted_state_authority=state_authority,
                ) as committed:
                    committed_yielded[0] = True
                    for authority in readback.files:
                        _verify_held_regular_file_authority(authority)
                    _validate_preflight_output_shape(
                        paths,
                        output_authorities,
                        require_complete=True,
                        allow_controls=False,
                    )
                    if committed.state != proposed:
                        raise RunnerError("committed preflight state changed")
                    return dict(committed.state)


def run_preflight(paths: RunnerPaths) -> dict[str, Any]:
    _assert_closed_environment()
    _validate_layout(paths)
    committed_build_returned = [False]
    with _classify_post_commit_unwind(
        committed_build_returned,
        boundary="outer",
    ):
        with material_pipeline_lock(paths) as material_authority:
            with _admit_recovered_state(
                paths,
                material_authority=material_authority,
            ) as state_authority:
                if type(state_authority) is _HeldCommittedStateAuthority:
                    with _read_committed_preflight_checkpoint(
                        paths,
                        material_authority=material_authority,
                        committed_state_authority=state_authority,
                    ):
                        pass
                    raise RunnerError(
                        "preflight is already complete at phase "
                        f"{state_authority.state['phase']}"
                    )
                if type(state_authority) is not _AdmittedStateAuthority:
                    raise RunnerError("preflight state admission type changed")
                result = _run_admitted_preflight_build(
                    paths,
                    material_authority=material_authority,
                    state_authority=state_authority,
                )
                committed_build_returned[0] = True
                return result


def _validate_bound_preflight_inputs(
    paths: RunnerPaths,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str]]:
    _validate_layout(paths)
    static_contents = tuple(
        _read_file_nofollow(_validate_input_path(paths, path))
        for path in _static_preflight_paths(paths)
    )
    configuration = _validate_static_preflight_bytes(static_contents)
    ledger_path = _safe_path(
        paths.input_ledger_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    manifest_path = _safe_path(
        paths.split_manifest_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    ledger_bytes = _read_file_nofollow(ledger_path)
    manifest_bytes = _read_file_nofollow(manifest_path)
    if type(ledger_bytes) is not bytes or type(manifest_bytes) is not bytes:
        raise RunnerError("bound preflight reader did not return exact bytes")
    try:
        ledger = validate_phase_b_input_ledger(
            _load_json_object_bytes(ledger_bytes, "preflight input ledger")
        )
        split = validate_phase_b_split_manifest(
            _load_json_object_bytes(manifest_bytes, "preflight split manifest")
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"bound preflight validation failed: {error}") from error
    digests = {
        "configuration_sha256": _sha256_bytes(static_contents[0]),
        "environment_lock_sha256": _sha256_bytes(static_contents[1]),
        "input_ledger_sha256": _sha256_bytes(ledger_bytes),
        "split_manifest_sha256": _sha256_bytes(manifest_bytes),
    }
    return configuration, split, ledger, digests


def _revalidate_bound_preflight(
    paths: RunnerPaths,
    state: Mapping[str, Any],
) -> None:
    _config, _split, _ledger, digests = _validate_bound_preflight_inputs(paths)
    if any(digests[field] != state[field] for field in digests):
        raise RunnerError("preflight anchor changed after validation")


def _validated_split_manifest_identity(
    paths: RunnerPaths,
    state: Mapping[str, Any],
) -> str:
    expected_file_sha256 = _validate_digest(
        state["split_manifest_sha256"],
        "split_manifest_sha256",
    )
    split_path = _safe_path(
        paths.split_manifest_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    split_bytes = _read_file_nofollow(split_path)
    if _sha256_bytes(split_bytes) != expected_file_sha256:
        raise RunnerError("split manifest changed after preflight")
    try:
        split = validate_phase_b_split_manifest(
            _load_json_object_bytes(split_bytes, "split manifest")
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(
            f"preflight split manifest validation failed: {error}"
        ) from error
    return split["split_manifest_sha256"]


def _validate_non_lockbox_packet_for_authority(
    paths: RunnerPaths,
    packet: Mapping[str, Any],
    *,
    expected_split_manifest_sha256: str,
) -> dict[str, Any]:
    _validate_digest(
        expected_split_manifest_sha256,
        "split_manifest_sha256",
    )
    if paths.authority not in {"production", "injected-test"}:
        raise RunnerError("runner path authority is invalid")
    label = (
        "production non-lockbox packet"
        if paths.authority == "production"
        else "synthetic non-lockbox packet"
    )
    try:
        from scripts.emotion_state_phase_b_public_pipeline import (
            validate_non_lockbox_review_packet,
        )

        public_validated = validate_non_lockbox_review_packet(packet)
        independent_validated = validate_non_lockbox_packet(packet)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid {label}: {error}") from error
    if public_validated != independent_validated:
        raise RunnerError("non-lockbox packet validators disagree")
    if public_validated["split_manifest_sha256"] != expected_split_manifest_sha256:
        raise RunnerError("split manifest identity does not match preflight state")
    return public_validated


def _validated_packet(
    paths: RunnerPaths,
    state: Mapping[str, Any],
    *,
    require_bound: bool,
) -> tuple[dict[str, Any], str]:
    packet_path = _validate_non_lockbox_path(paths)
    digest_before = _sha256_file(packet_path)
    packet = _load_json_object(packet_path, "non-lockbox packet")
    validated_split_manifest_sha256 = _validated_split_manifest_identity(
        paths,
        state,
    )
    validated = _validate_non_lockbox_packet_for_authority(
        paths,
        packet,
        expected_split_manifest_sha256=validated_split_manifest_sha256,
    )
    digest = _sha256_file(packet_path)
    if digest != digest_before:
        raise RunnerError("non-lockbox packet changed during semantic validation")
    if require_bound and digest != state["non_lockbox_packet_sha256"]:
        raise RunnerError("non-lockbox packet changed after validation")
    return validated, digest


def _classify_non_lockbox_checkpoint_phase(
    preflight_readback: _CommittedPreflightReadback,
) -> Literal["build", "committed"]:
    if type(preflight_readback) is not _CommittedPreflightReadback:
        raise RunnerError("committed preflight readback type changed")
    phase = preflight_readback.state.get("phase")
    if phase == "preflight_complete":
        return "build"
    if phase in {
        "non_lockbox_complete",
        "lockbox_complete",
        "awaiting_acceptance",
        "accepted",
        "rejected",
    }:
        return "committed"
    raise RunnerError(f"non-lockbox cannot run from phase {phase}")


def _non_lockbox_preflight_placeholders_are_unopened(
    state: Mapping[str, Any],
) -> bool:
    return not (
        type(state) is not dict
        or state.get("phase") != "preflight_complete"
        or state.get("non_lockbox_packet_sha256") != UNSET_DIGEST
        or state.get("lockbox_open_count") != 0
        or state.get("lockbox_result_sha256") != UNSET_DIGEST
        or state.get("lockbox_decision_evidence_sha256") != UNSET_DIGEST
        or state.get("lockbox_decision_evidence_mint_sha256") != UNSET_DIGEST
        or state.get("candidate_transaction_id") != ""
    )


def _require_non_lockbox_preflight_placeholders(
    state: Mapping[str, Any],
) -> None:
    if not _non_lockbox_preflight_placeholders_are_unopened(state):
        raise RunnerError("preflight state placeholders are not unopened")


def _validated_static_non_lockbox_mappings(
    static_inputs: _HeldStaticPreflightInputs,
    *,
    state: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if (
        type(state) is not dict
        or static_inputs.digests[0] != state.get("configuration_sha256")
        or static_inputs.digests[1] != state.get("environment_lock_sha256")
    ):
        raise RunnerError("held static bytes do not match committed state")
    try:
        mappings = (
            validate_config(_load_json_object_bytes(
                static_inputs.contents[0],
                "non-lockbox configuration",
            )),
            validate_environment_lock(_load_json_object_bytes(
                static_inputs.contents[1],
                "non-lockbox environment lock",
            )),
            validate_feature_schema(_load_json_object_bytes(
                static_inputs.contents[2],
                "non-lockbox feature schema",
            )),
            validate_split_schema(_load_json_object_bytes(
                static_inputs.contents[3],
                "non-lockbox split schema",
            )),
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"held non-lockbox static semantics changed: {error}") from error
    identity_fields = (
        "configuration_sha256",
        "environment_lock_sha256",
        "feature_schema_sha256",
        "split_schema_sha256",
    )
    identities = tuple(canonical_payload_sha256(mapping) for mapping in mappings)
    if (
        mappings[0] != static_inputs.configuration
        or identities
        != tuple(EXPECTED_EVIDENCE_IDENTITY_SHA256[field] for field in identity_fields)
        or split_manifest.get("configuration_sha256") != identities[0]
    ):
        raise RunnerError("held static semantic identity changed")
    try:
        bound_configuration, bound_feature_schema = (
            validate_config_feature_schema_binding(mappings[0], mappings[2])
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(
            f"held non-lockbox static semantics changed: {error}"
        ) from error
    mappings = (
        bound_configuration,
        mappings[1],
        bound_feature_schema,
        mappings[3],
    )
    return tuple(deepcopy(mapping) for mapping in mappings)  # type: ignore[return-value]


def _validate_first_build_environment_inputs(
    static_inputs: _HeldStaticPreflightInputs,
    wheel_inputs: _HeldEnvironmentWheelInputs,
) -> dict[str, Any]:
    if type(static_inputs) is not _HeldStaticPreflightInputs:
        raise RunnerError("held static-input authority type changed")
    _revalidate_held_environment_wheel_inputs(wheel_inputs)
    wheel_bytes = dict(zip(
        wheel_inputs.filenames,
        wheel_inputs.contents,
        strict=True,
    ))
    try:
        report = validate_environment_identity_bytes(
            static_inputs.contents[1],
            wheel_bytes,
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"held environment identity is invalid: {error}") from error
    if type(report) is not dict:
        raise RunnerError("held environment identity report type changed")
    _revalidate_held_environment_wheel_inputs(wheel_inputs)
    return deepcopy(report)


def _validate_first_build_non_lockbox_artifacts(
    paths: RunnerPaths,
    artifacts: ProductionNonLockboxArtifacts,
    *,
    tracked_public_authority_commitment_sha256: str,
) -> tuple[tuple[Path, bytes], ...]:
    expected_commitment = _validate_digest(
        tracked_public_authority_commitment_sha256,
        "tracked public authority commitment",
    )
    payload_bytes = _non_lockbox_payload_bytes(paths, artifacts)
    copies = (
        *(artifacts.feature_caches[role].get(
            "tracked_public_authority_commitment_sha256"
        ) for role in NONFINAL_PARTITION_ROLES),
        artifacts.ami_evidence.get(
            "tracked_public_authority_commitment_sha256"
        ),
        artifacts.review_packet.get(
            "tracked_public_authority_commitment_sha256"
        ),
    )
    if any(copy != expected_commitment for copy in copies):
        raise RunnerError("built tracked-public commitment copies changed")
    return payload_bytes


def _restore_and_compare_non_lockbox_readback(
    paths: RunnerPaths,
    readback: _PersistedNonLockboxReadback,
    *,
    authorities: Mapping[str, "ValidatedPartitionAuthority"],
    split_manifest: Mapping[str, Any],
    static_mappings: tuple[
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
        dict[str, Any],
    ],
) -> ProductionNonLockboxArtifacts:
    if (
        type(readback) is not _PersistedNonLockboxReadback
        or type(authorities) is not dict
        or tuple(authorities) != NONFINAL_PARTITION_ROLES
        or type(static_mappings) is not tuple
        or len(static_mappings) != 4
    ):
        raise RunnerError("non-lockbox semantic readback capability changed")
    configuration, environment_lock, feature_schema, split_schema = (
        static_mappings
    )
    try:
        restored = restore_production_non_lockbox_artifacts(
            authorities=dict(authorities),
            split_manifest=deepcopy(split_manifest),
            feature_caches={
                role: deepcopy(payload)
                for role, payload in zip(
                    NONFINAL_PARTITION_ROLES,
                    readback.feature_caches,
                    strict=True,
                )
            },
            ami_evidence=deepcopy(readback.ami_evidence),
            review_packet=deepcopy(readback.review_packet),
            configuration=deepcopy(configuration),
            environment_lock=deepcopy(environment_lock),
            feature_schema=deepcopy(feature_schema),
            split_schema=deepcopy(split_schema),
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"non-lockbox semantic restore failed: {error}") from error
    expected = _non_lockbox_payload_bytes(paths, restored)
    retained = tuple(
        _read_held_regular_file_bytes(file) for file in readback.files
    )
    if tuple(content for _path, content in expected) != retained:
        raise RunnerError("non-lockbox semantic restore changed retained bytes")
    if readback.files[-1].sha256 != _sha256_bytes(retained[-1]):
        raise RunnerError("non-lockbox packet retained-file identity changed")
    return restored


def _revalidate_non_lockbox_first_build_capabilities(
    paths: RunnerPaths,
    *,
    material_authority: _MaterialPipelineAuthority,
    committed_preflight: _HeldCommittedStateAuthority,
    preflight_readback: _CommittedPreflightReadback,
    admitted_state: _AdmittedNonLockboxStateAuthority,
    static_inputs: _HeldStaticPreflightInputs,
    wheel_inputs: _HeldEnvironmentWheelInputs,
    evidence_inputs: _HeldTrackedPublicEvidenceInputs,
    output_authorities: _NonLockboxOutputAuthorities,
    non_lockbox_readback: _PersistedNonLockboxReadback,
    committed_non_lockbox: _HeldCommittedStateAuthority | None = None,
    expected_state: Mapping[str, Any] | None = None,
) -> None:
    _verify_material_pipeline_authority(material_authority)
    _revalidate_held_static_preflight_inputs(static_inputs)
    _revalidate_held_environment_wheel_inputs(wheel_inputs)
    _revalidate_held_tracked_public_evidence_inputs(evidence_inputs)
    ledger, manifest, restored = _validate_and_restore_readback_files(
        paths,
        preflight_readback.artifacts.files,
    )
    if (
        ledger != preflight_readback.artifacts.input_ledger
        or manifest != preflight_readback.artifacts.split_manifest
        or any(
            actual.to_payload() != retained.to_payload()
            for actual, retained in zip(
                restored,
                preflight_readback.restored,
                strict=True,
            )
        )
    ):
        raise RunnerError("retained preflight capability changed")
    _validate_non_lockbox_output_shape(
        paths,
        output_authorities,
        require_complete=True,
        allow_controls=False,
    )
    replay = _validate_non_lockbox_readback_files(
        paths,
        non_lockbox_readback.files,
    )
    if replay != (
        non_lockbox_readback.feature_caches,
        non_lockbox_readback.ami_evidence,
        non_lockbox_readback.review_packet,
    ):
        raise RunnerError("retained non-lockbox capability changed")
    if committed_non_lockbox is None:
        _verify_admitted_non_lockbox_state_cas(
            paths,
            admitted_state,
            state_root=material_authority.state_root,
        )
        if committed_preflight._file_owner.peek() is not committed_preflight.file:
            raise RunnerError("preflight state owner changed before commit")
    else:
        if (
            type(committed_non_lockbox) is not _HeldCommittedStateAuthority
            or type(expected_state) is not dict
            or committed_non_lockbox.state != expected_state
            or committed_non_lockbox._file_owner.peek()
            is not committed_non_lockbox.file
        ):
            raise RunnerError("committed non-lockbox state capability changed")
        _verify_held_regular_file_authority(committed_non_lockbox.file)
        state, state_bytes = _state_from_held_file(committed_non_lockbox.file)
        if (
            state != expected_state
            or state_bytes != canonical_json_bytes(expected_state)
        ):
            raise RunnerError("committed non-lockbox state bytes changed")
    _validate_state_root_allowlist(
        paths,
        material_authority.state_root,
        allow_state_controls=False,
    )


def _proposed_non_lockbox_complete_state(
    admitted_state: _AdmittedNonLockboxStateAuthority,
    *,
    packet_file_sha256: str,
) -> dict[str, Any]:
    if type(admitted_state) is not _AdmittedNonLockboxStateAuthority:
        raise RunnerError("admitted non-lockbox state capability changed")
    if not _non_lockbox_preflight_placeholders_are_unopened(
        admitted_state.initial_state
    ):
        raise RunnerError("preflight state placeholders are not unopened")
    packet_digest = _validate_digest(
        packet_file_sha256,
        "non-lockbox packet file",
    )
    proposed = dict(admitted_state.initial_state)
    proposed.update({
        "phase": "non_lockbox_complete",
        "non_lockbox_packet_sha256": packet_digest,
    })
    proposed = _validate_state(proposed)
    changed = {
        key
        for key in proposed
        if proposed[key] != admitted_state.initial_state[key]
    }
    if changed != {"phase", "non_lockbox_packet_sha256"}:
        raise RunnerError("non-lockbox proposed state changed extra fields")
    return proposed


@contextmanager
def _classify_non_lockbox_post_commit_unwind(
    marker: list[bool],
) -> Iterator[None]:
    try:
        yield
    except Exception as error:
        if marker == [True]:
            if isinstance(error, RunnerError) and "indeterminate" in str(error):
                raise
            raise RunnerError(
                "non-lockbox state outcome is indeterminate during "
                f"post-commit outer unwind: {error}"
            ) from error
        raise


def _run_production_non_lockbox_lane(paths: RunnerPaths) -> dict[str, Any]:
    """Run the locked first-build/retry lane after entry boundary checks."""
    _validate_layout(paths)
    post_commit = [False]
    result: dict[str, Any] | None = None
    with _classify_non_lockbox_post_commit_unwind(post_commit):
        with material_pipeline_lock(paths) as material_authority:
            with _admit_recovered_state(
                paths,
                material_authority=material_authority,
            ) as committed_preflight:
                if type(committed_preflight) is not _HeldCommittedStateAuthority:
                    raise RunnerError(
                        "non-lockbox requires a committed preflight checkpoint"
                    )
                with _read_committed_preflight_checkpoint(
                    paths,
                    material_authority=material_authority,
                    committed_state_authority=committed_preflight,
                ) as preflight_readback:
                    split_manifest, authorities, records_by_role = (
                        _validate_runner_non_lockbox_role_algebra(
                            preflight_readback
                        )
                    )
                    checkpoint_phase = _classify_non_lockbox_checkpoint_phase(
                        preflight_readback
                    )
                    if checkpoint_phase == "committed":
                        with _read_committed_non_lockbox_checkpoint(
                            paths,
                            material_authority=material_authority,
                            committed_state_authority=committed_preflight,
                            preflight_readback=preflight_readback,
                        ):
                            pass
                        raise RunnerError(
                            "non-lockbox checkpoint is already complete from phase "
                            f"{preflight_readback.state['phase']}"
                        )

                    _require_non_lockbox_preflight_placeholders(
                        preflight_readback.state
                    )
                    with _admit_non_lockbox_state(
                        paths,
                        material_authority=material_authority,
                        committed_state_authority=committed_preflight,
                    ) as admitted_state:
                        with _held_preflight_static_inputs(
                            paths
                        ) as static_inputs, _held_environment_wheel_inputs(
                            paths
                        ) as wheel_inputs:
                            static_mappings = (
                                _validated_static_non_lockbox_mappings(
                                    static_inputs,
                                    state=preflight_readback.state,
                                    split_manifest=split_manifest,
                                )
                            )
                            _validate_first_build_environment_inputs(
                                static_inputs,
                                wheel_inputs,
                            )
                            with _held_tracked_public_evidence_inputs(
                                paths
                            ) as evidence_inputs:
                                tracked_authority, tracked_commitment = (
                                    _tracked_public_authority_from_held_evidence(
                                        evidence_inputs
                                    )
                                )
                                audio_by_role = (
                                    _derive_runner_non_lockbox_audio_source_identities(
                                        tracked_authority,
                                        records_by_role,
                                    )
                                )
                                ami_sources = (
                                    _derive_runner_non_lockbox_ami_source_identities(
                                        tracked_authority,
                                        records_by_role,
                                    )
                                )
                                audio_sources = tuple(
                                    source
                                    for role in NONFINAL_PARTITION_ROLES
                                    for source in audio_by_role[role]
                                )
                                audio_reader = (
                                    _frozen_non_lockbox_public_source_reader(
                                        paths,
                                        audio_sources,
                                        family="crema_wav",
                                    )
                                )
                                ami_reader = (
                                    _frozen_non_lockbox_public_source_reader(
                                        paths,
                                        ami_sources,
                                        family="ami_xml",
                                    )
                                )
                                tracked_evidence = dict(zip(
                                    evidence_inputs.names,
                                    evidence_inputs.contents,
                                    strict=True,
                                ))
                                try:
                                    artifacts = (
                                        build_production_non_lockbox_artifacts(
                                            authorities=dict(authorities),
                                            split_manifest=deepcopy(
                                                split_manifest
                                            ),
                                            read_verified_audio=audio_reader,
                                            read_verified_ami=ami_reader,
                                            tracked_evidence=tracked_evidence,
                                            tracked_authority=tracked_authority,
                                            configuration=deepcopy(
                                                static_mappings[0]
                                            ),
                                            environment_lock=deepcopy(
                                                static_mappings[1]
                                            ),
                                            feature_schema=deepcopy(
                                                static_mappings[2]
                                            ),
                                            split_schema=deepcopy(
                                                static_mappings[3]
                                            ),
                                        )
                                    )
                                except (TypeError, ValueError) as error:
                                    raise RunnerError(
                                        "production non-lockbox build failed: "
                                        f"{error}"
                                    ) from error
                                _validate_first_build_non_lockbox_artifacts(
                                    paths,
                                    artifacts,
                                    tracked_public_authority_commitment_sha256=(
                                        tracked_commitment
                                    ),
                                )
                                with _held_non_lockbox_output_authorities(
                                    paths,
                                    material_authority,
                                ) as output_authorities:
                                    with _persist_non_lockbox_artifacts(
                                        paths,
                                        artifacts,
                                        material_authority=material_authority,
                                        output_authorities=output_authorities,
                                    ) as non_lockbox_readback:
                                        _restore_and_compare_non_lockbox_readback(
                                            paths,
                                            non_lockbox_readback,
                                            authorities=authorities,
                                            split_manifest=split_manifest,
                                            static_mappings=static_mappings,
                                        )
                                        validate_installed_environment_identity()
                                        _assert_closed_environment()
                                        _revalidate_non_lockbox_first_build_capabilities(
                                            paths,
                                            material_authority=material_authority,
                                            committed_preflight=committed_preflight,
                                            preflight_readback=preflight_readback,
                                            admitted_state=admitted_state,
                                            static_inputs=static_inputs,
                                            wheel_inputs=wheel_inputs,
                                            evidence_inputs=evidence_inputs,
                                            output_authorities=output_authorities,
                                            non_lockbox_readback=(
                                                non_lockbox_readback
                                            ),
                                        )
                                        proposed_state = (
                                            _proposed_non_lockbox_complete_state(
                                                admitted_state,
                                                packet_file_sha256=(
                                                    non_lockbox_readback.files[
                                                        -1
                                                    ].sha256
                                                ),
                                            )
                                        )
                                        with _commit_non_lockbox_state_durably(
                                            paths,
                                            proposed_state,
                                            material_authority=material_authority,
                                            admitted_state_authority=(
                                                admitted_state
                                            ),
                                        ) as committed_non_lockbox:
                                            post_commit[0] = True
                                            _revalidate_non_lockbox_first_build_capabilities(
                                                paths,
                                                material_authority=(
                                                    material_authority
                                                ),
                                                committed_preflight=(
                                                    committed_preflight
                                                ),
                                                preflight_readback=(
                                                    preflight_readback
                                                ),
                                                admitted_state=admitted_state,
                                                static_inputs=static_inputs,
                                                wheel_inputs=wheel_inputs,
                                                evidence_inputs=evidence_inputs,
                                                output_authorities=(
                                                    output_authorities
                                                ),
                                                non_lockbox_readback=(
                                                    non_lockbox_readback
                                                ),
                                                committed_non_lockbox=(
                                                    committed_non_lockbox
                                                ),
                                                expected_state=proposed_state,
                                            )
                                            result = deepcopy(
                                                committed_non_lockbox.state
                                            )
    if result is None:
        raise RunnerError("non-lockbox lane did not commit a state")
    return result


def run_non_lockbox(paths: RunnerPaths) -> dict[str, Any]:
    validate_installed_environment_identity()
    _assert_closed_environment()
    return _run_production_non_lockbox_lane(paths)


def _open_lock_handle(path: Path, *, create: bool = True) -> BinaryIO:
    _require_mutation_path_proof(path)
    if not os.path.lexists(path):
        if not create:
            raise RunnerError("required publication lock is missing")
        try:
            _write_new_fsynced(path, b"")
        except RunnerError:
            if not os.path.lexists(path):
                raise
    flags = os.O_RDWR | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        with _trusted_parent_handles(path) as parent_authority:
            parent_descriptor = parent_authority.posix_descriptor
            _verify_cached_path_proof(path)
            if parent_descriptor is None:
                before = os.stat(path, follow_symlinks=False)
                descriptor = os.open(path, flags)
                after = os.stat(path, follow_symlinks=False)
            else:
                before = os.stat(
                    path.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                descriptor = os.open(
                    path.name,
                    flags,
                    dir_fd=parent_descriptor,
                )
                after = os.stat(
                    path.name,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            opened = os.fstat(descriptor)
            _verify_cached_path_proof(path)
        if opened.st_nlink != 1:
            os.close(descriptor)
            raise RunnerError("lock file must have a single-link identity")
        if (
            _is_link_or_reparse(path, after)
            or (before.st_dev, before.st_ino)
            != (opened.st_dev, opened.st_ino)
            or (after.st_dev, after.st_ino)
            != (opened.st_dev, opened.st_ino)
        ):
            os.close(descriptor)
            raise RunnerError("lock file identity changed during open")
        return os.fdopen(descriptor, "r+b", closefd=True)
    except OSError as error:
        raise RunnerError("unable to open OS-backed lock") from error


@contextmanager
def lockbox_lock(paths: RunnerPaths) -> Iterator[None]:
    _validate_layout(paths)
    _ensure_directory_durable(Path(paths.state_root))
    lock_path = _safe_path(
        paths.lockbox_lock_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
    )
    if os.path.lexists(lock_path):
        _safe_path(
            lock_path,
            allowed_root=paths.state_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
    handle = _open_lock_handle(lock_path)
    acquired = False
    try:
        try:
            _acquire_os_lock(handle)
        except OSError as error:
            raise RunnerError("lockbox lock is already held or unavailable") from error
        acquired = True
        _recover_output_replacement(
            paths,
            paths.lockbox_reservation_path,
            allowed_root=paths.state_root,
        )
        _recover_output_replacement(
            paths,
            _resolve_final_lockbox_result_path(paths),
            allowed_root=paths.lockbox_root,
        )
        yield
    finally:
        if acquired:
            try:
                _release_os_lock(handle)
            except OSError:
                pass
        handle.close()


def _reservation_payload(
    state: Mapping[str, Any],
    *,
    transaction_id: str,
    status: str,
    lockbox_result_sha256: str,
    lockbox_decision_evidence_sha256: str,
    lockbox_decision_evidence_mint_sha256: str,
) -> dict[str, Any]:
    if status not in {"reserved", "completed"}:
        raise RunnerError("invalid lockbox reservation status")
    if status == "reserved":
        if any(
            digest != UNSET_DIGEST
            for digest in (
                lockbox_result_sha256,
                lockbox_decision_evidence_sha256,
                lockbox_decision_evidence_mint_sha256,
            )
        ):
            raise RunnerError("reserved lockbox cannot bind minted evidence bytes")
    else:
        for label, digest in (
            ("result", lockbox_result_sha256),
            ("decision evidence", lockbox_decision_evidence_sha256),
            (
                "private decision evidence mint",
                lockbox_decision_evidence_mint_sha256,
            ),
        ):
            _validate_digest(digest, f"lockbox reservation {label}")
            if digest == UNSET_DIGEST:
                raise RunnerError(
                    "completed lockbox reservation needs minted evidence bytes"
                )
    return {
        "schema_version": 1,
        "transaction_id": _validate_transaction_id(transaction_id),
        "status": status,
        "configuration_sha256": state["configuration_sha256"],
        "environment_lock_sha256": state["environment_lock_sha256"],
        "input_ledger_sha256": state["input_ledger_sha256"],
        "split_manifest_sha256": state["split_manifest_sha256"],
        "non_lockbox_packet_sha256": state["non_lockbox_packet_sha256"],
        "lockbox_result_sha256": lockbox_result_sha256,
        "lockbox_decision_evidence_sha256": (
            lockbox_decision_evidence_sha256
        ),
        "lockbox_decision_evidence_mint_sha256": (
            lockbox_decision_evidence_mint_sha256
        ),
    }


def _validate_reservation(payload: Any) -> dict[str, Any]:
    expected = {
        "schema_version",
        "transaction_id",
        "status",
        "configuration_sha256",
        "environment_lock_sha256",
        "input_ledger_sha256",
        "split_manifest_sha256",
        "non_lockbox_packet_sha256",
        "lockbox_result_sha256",
        "lockbox_decision_evidence_sha256",
        "lockbox_decision_evidence_mint_sha256",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise RunnerError("invalid lockbox reservation fields")
    if payload["schema_version"] != 1 or type(payload["schema_version"]) is not int:
        raise RunnerError("invalid lockbox reservation schema")
    return _reservation_payload(
        payload,
        transaction_id=payload["transaction_id"],
        status=payload["status"],
        lockbox_result_sha256=payload["lockbox_result_sha256"],
        lockbox_decision_evidence_sha256=payload[
            "lockbox_decision_evidence_sha256"
        ],
        lockbox_decision_evidence_mint_sha256=payload[
            "lockbox_decision_evidence_mint_sha256"
        ],
    )


def _load_reservation(
    paths: RunnerPaths,
    *,
    recover: bool = True,
) -> dict[str, Any]:
    if recover:
        _recover_output_replacement(
            paths,
            paths.lockbox_reservation_path,
            allowed_root=paths.state_root,
        )
    reservation_path = _safe_path(
        paths.lockbox_reservation_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    return _validate_reservation(
        _load_json_object(reservation_path, "lockbox reservation")
    )


def _validated_private_decision_evidence(
    decision_evidence: Any,
) -> tuple[dict[str, Any], str, str, str]:
    from scripts.emotion_state_phase_b_evaluation import decide_experiment

    try:
        authoritative_decision = decide_experiment(
            decision_evidence,
            dict(EXPECTED_VALIDITY),
        )
        payload = decision_evidence.to_payload()
        validate_decision_inputs(payload, dict(EXPECTED_VALIDITY))
        evidence_mint_sha256 = decision_evidence.mint_sha256
    except (AttributeError, TypeError, ValueError) as error:
        raise RunnerError(
            "private DecisionEvidence mint and recursive lineage are required"
        ) from error
    if derive_phase_b_decision(payload) != authoritative_decision:
        raise RunnerError("private decision and structural readback disagree")
    if (
        serialized_decision_evidence_mint_sha256(payload)
        != evidence_mint_sha256
    ):
        raise RunnerError("private DecisionEvidence mint digest changed")
    return (
        payload,
        authoritative_decision,
        _mapping_digest(payload),
        evidence_mint_sha256,
    )


def run_lockbox(paths: RunnerPaths) -> dict[str, Any]:
    _assert_closed_environment()
    _validate_layout(paths)
    raise RunnerError(
        "production lockbox evaluator is not wired; "
        "a private DecisionEvidence mint is required"
    )


def _run_lockbox_with_private_evidence_for_testing(
    paths: RunnerPaths,
    decision_evidence: Any,
) -> dict[str, Any]:
    if paths.authority != "injected-test":
        raise RunnerError("private synthetic lockbox mint is test-only")
    _assert_closed_environment()
    (
        decision_payload,
        authoritative_decision,
        decision_evidence_sha256,
        decision_evidence_mint_sha256,
    ) = _validated_private_decision_evidence(decision_evidence)
    with lockbox_lock(paths):
        state = load_state(paths)
        _require_phase(state, "non_lockbox_complete")
        if state["lockbox_open_count"] != 0:
            raise RunnerError("final lockbox has already been opened")
        _revalidate_bound_preflight(paths, state)
        _validated_packet(paths, state, require_bound=True)
        if os.path.lexists(paths.lockbox_reservation_path):
            _load_reservation(paths)
            raise RunnerError("final lockbox experiment version is already reserved")

        transaction_id = uuid.uuid4().hex
        reservation = _reservation_payload(
            state,
            transaction_id=transaction_id,
            status="reserved",
            lockbox_result_sha256=UNSET_DIGEST,
            lockbox_decision_evidence_sha256=UNSET_DIGEST,
            lockbox_decision_evidence_mint_sha256=UNSET_DIGEST,
        )
        _safe_path(
            paths.lockbox_reservation_path,
            allowed_root=paths.state_root,
            project_root=paths.project_root,
        )
        _replace_bytes_durably(
            paths.lockbox_reservation_path,
            canonical_json_bytes(reservation),
        )
        if _load_reservation(paths) != reservation:
            raise RunnerError("lockbox reservation readback mismatch")

        lockbox_path = _validate_lockbox_path(paths)
        try:
            lockbox_input = _load_json_object(lockbox_path, "lockbox AMI input")
            split_manifest = _load_json_object(
                paths.split_manifest_path,
                "split manifest",
            )
            validated_ami = validate_lockbox_ami_input(lockbox_input)
            lockbox_result = {
                "schema_version": 1,
                "decision_evidence": decision_payload,
                "ami": validated_ami["ami"],
            }
            validate_lockbox_lineage(lockbox_result, split_manifest)
        except (TypeError, ValueError) as error:
            raise RunnerError(f"invalid lockbox result: {error}") from error
        if derive_phase_b_decision(decision_payload) != authoritative_decision:
            raise RunnerError("private decision changed before serialization")
        result_bytes = canonical_json_bytes(lockbox_result)
        _replace_bytes_durably(lockbox_path, result_bytes)
        if _read_file_nofollow(lockbox_path) != result_bytes:
            raise RunnerError("lockbox result changed after internal serialization")
        result_digest = _sha256_file(lockbox_path)

        _revalidate_bound_preflight(paths, state)
        _validated_packet(paths, state, require_bound=True)
        second_result = _load_json_object(lockbox_path, "lockbox result")
        try:
            second_split = _load_json_object(
                paths.split_manifest_path,
                "split manifest",
            )
            validate_lockbox_lineage(second_result, second_split)
        except (TypeError, ValueError) as error:
            raise RunnerError(f"invalid lockbox result: {error}") from error
        if (
            _sha256_file(lockbox_path) != result_digest
            or second_result != lockbox_result
            or _mapping_digest(second_result["decision_evidence"])
            != decision_evidence_sha256
            or serialized_decision_evidence_mint_sha256(
                second_result["decision_evidence"]
            )
            != decision_evidence_mint_sha256
        ):
            raise RunnerError("lockbox result changed during reserved validation")
        _assert_closed_environment()

        completed = _reservation_payload(
            state,
            transaction_id=transaction_id,
            status="completed",
            lockbox_result_sha256=result_digest,
            lockbox_decision_evidence_sha256=decision_evidence_sha256,
            lockbox_decision_evidence_mint_sha256=(
                decision_evidence_mint_sha256
            ),
        )
        _replace_bytes_durably(
            paths.lockbox_reservation_path,
            canonical_json_bytes(completed),
        )
        if _load_reservation(paths) != completed:
            raise RunnerError("completed lockbox reservation readback mismatch")
        return _transition(
            paths,
            state,
            "lockbox_complete",
            lockbox_open_count=1,
            lockbox_result_sha256=result_digest,
            lockbox_decision_evidence_sha256=decision_evidence_sha256,
            lockbox_decision_evidence_mint_sha256=(
                decision_evidence_mint_sha256
            ),
        )


def build_aggregate_result(
    paths: RunnerPaths,
    *,
    read_only: bool = False,
) -> dict[str, Any]:
    state = load_state(paths, recover=not read_only)
    if state["phase"] not in {
        "lockbox_complete",
        "awaiting_acceptance",
        "accepted",
        "rejected",
    }:
        raise RunnerError("aggregate result requires a completed lockbox")
    _revalidate_bound_preflight(paths, state)
    config_path = _validate_input_path(paths, paths.config_path)
    feature_path = _validate_input_path(paths, paths.feature_schema_path)
    split_schema_path = _validate_input_path(paths, paths.split_schema_path)
    split_path = _safe_path(
        paths.split_manifest_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    ledger_path = _safe_path(
        paths.input_ledger_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    packet_path = _validate_non_lockbox_path(paths)
    lockbox_path = _validate_lockbox_path(paths)
    if _sha256_file(packet_path) != state["non_lockbox_packet_sha256"]:
        raise RunnerError("non-lockbox packet digest mismatch")
    if _sha256_file(lockbox_path) != state["lockbox_result_sha256"]:
        raise RunnerError("lockbox result digest mismatch")
    try:
        config = validate_config(_load_json_object(config_path, "configuration"))
        feature = validate_feature_schema(
            _load_json_object(feature_path, "feature schema")
        )
        config, feature = validate_config_feature_schema_binding(config, feature)
        validate_split_schema(
            _load_json_object(split_schema_path, "split schema")
        )
        split_evidence = validate_phase_b_split_manifest(
            _load_json_object(split_path, "split manifest")
        )
        ledger = validate_phase_b_input_ledger(
            _load_json_object(ledger_path, "input ledger")
        )
        packet = validate_non_lockbox_packet(
            _load_json_object(packet_path, "non-lockbox packet")
        )
        lockbox_payload = _load_json_object(lockbox_path, "lockbox result")
        validate_lockbox_result(lockbox_payload)
        lockbox = validated_lockbox_summary(
            lockbox_payload,
            bound_decision_evidence_sha256=state[
                "lockbox_decision_evidence_sha256"
            ],
            bound_decision_evidence_mint_sha256=state[
                "lockbox_decision_evidence_mint_sha256"
            ],
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"aggregate input validation failed: {error}") from error
    reservation = _load_reservation(paths, recover=not read_only)
    if (
        reservation["status"] != "completed"
        or reservation["lockbox_result_sha256"]
        != state["lockbox_result_sha256"]
        or any(
            reservation[field] != state[field]
            for field in (
                "configuration_sha256",
                "environment_lock_sha256",
                "input_ledger_sha256",
                "split_manifest_sha256",
                "non_lockbox_packet_sha256",
                "lockbox_decision_evidence_sha256",
                "lockbox_decision_evidence_mint_sha256",
            )
        )
    ):
        raise RunnerError("completed lockbox reservation does not bind state")
    reservation_sha256 = _sha256_file(paths.lockbox_reservation_path)
    result = {
        "schema_id": "emotion-state-002-phase-b-result-v1",
        "schema_version": 1,
        "checkpoint_id": config["checkpoint_id"],
        "phase_a": ledger["phase_a"],
        "dataset_evidence": ledger["dataset_evidence"],
        "raw_csv_sha256": {
            "finished_response_votes": ledger["raw_csv_sha256"][
                "finishedResponses.csv"
            ],
            "summary_voice_votes": ledger["raw_csv_sha256"][
                "processedResults/summaryTable.csv"
            ],
        },
        "configuration_sha256": state["configuration_sha256"],
        "environment_lock_sha256": state["environment_lock_sha256"],
        "feature_schema_sha256": _sha256_file(feature_path),
        "split_schema_sha256": _sha256_file(split_schema_path),
        "split_manifest_sha256": state["split_manifest_sha256"],
        "split_evidence": split_evidence,
        "crema_label_ledger": ledger["crema_label_ledger"],
        "model_settings": packet["model_settings"],
        "metric_definitions": packet["metric_definitions"],
        "slice_definitions": packet["slice_definitions"],
        "non_lockbox_review_sha256": packet["review_sha256"],
        "lockbox": {
            "open_count": state["lockbox_open_count"],
            "reservation_sha256": reservation_sha256,
            "result_sha256": state["lockbox_result_sha256"],
            "decision_evidence_sha256": state[
                "lockbox_decision_evidence_sha256"
            ],
            "decision_evidence_mint_sha256": state[
                "lockbox_decision_evidence_mint_sha256"
            ],
            "crema": lockbox["crema"],
            "ami": lockbox["ami"],
        },
        "validity": lockbox["validity"],
        "decision": lockbox["decision"],
        "closed_boundaries": config["boundaries"],
    }
    if result["raw_csv_sha256"] != EXPECTED_PUBLIC_RAW_SOURCE_SHA256:
        raise RunnerError("published raw-source projection is invalid")
    del feature
    _revalidate_bound_preflight(paths, state)
    _validated_packet(paths, state, require_bound=True)
    if (
        _sha256_file(lockbox_path) != state["lockbox_result_sha256"]
        or _sha256_file(paths.lockbox_reservation_path) != reservation_sha256
    ):
        raise RunnerError("aggregate inputs changed during validation")
    try:
        return validate_phase_b_result(result)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"aggregate result validation failed: {error}") from error


def render_report(result: Mapping[str, Any], result_sha256: str) -> str:
    _validate_digest(result_sha256, "result_sha256")
    try:
        validated = validate_phase_b_result(dict(result))
    except (TypeError, ValueError) as error:
        raise RunnerError(f"report result is invalid: {error}") from error
    canonical_result_sha256 = _sha256_bytes(canonical_json_bytes(validated))
    if canonical_result_sha256 != result_sha256:
        raise RunnerError("report result digest does not match canonical JSON")
    canonical_payload = canonical_json_bytes(validated).decode("utf-8").rstrip("\n")
    return (
        "# EMOTION-STATE-002 Phase B public-data feasibility\n\n"
        f"- Result SHA-256: `{result_sha256}`\n"
        f"- Decision: `{validated['decision']}`\n"
        "- Final lockbox open count: `1`\n"
        "- Boundary: aggregate public/synthetic evidence only; no private data, "
        "provider operations, network evaluation, source adaptation, runtime "
        "influence, or customer-state output.\n\n"
        "## Canonical aggregate\n\n"
        "```json\n"
        f"{canonical_payload}\n"
        "```\n"
    )


def _transaction_paths(paths: RunnerPaths, transaction_id: str) -> dict[str, Path]:
    transaction_id = _validate_transaction_id(transaction_id)
    root = paths.recovery_root
    return {
        "new_result": root / f"{transaction_id}.result.stage",
        "new_report": root / f"{transaction_id}.report.stage",
        "previous_result": root / f"{transaction_id}.result.backup",
        "previous_report": root / f"{transaction_id}.report.backup",
        "restore_result": root / f"{transaction_id}.result.restore",
        "restore_report": root / f"{transaction_id}.report.restore",
        "journal_update": root / f"{transaction_id}.journal.stage",
    }


def _acquire_os_lock(
    handle: BinaryIO,
    *,
    initialize: bool = True,
) -> None:
    if os.name == "nt":
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            if not initialize:
                raise RunnerError(
                    "read-only publication lock is not initialized"
                )
            handle.write(b"\0")
            handle.flush()
            os.fsync(handle.fileno())
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _release_os_lock(handle: BinaryIO) -> None:
    if os.name == "nt":
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def publication_lock(
    paths: RunnerPaths,
    *,
    read_only: bool = False,
) -> Iterator[None]:
    _validate_layout(paths)
    if read_only:
        _safe_path(
            paths.recovery_root,
            allowed_root=paths.state_root,
            project_root=paths.project_root,
            final_kind="directory",
            require_final=True,
        )
    else:
        _ensure_directory_durable(Path(paths.recovery_root))
        _safe_path(
            paths.recovery_root,
            allowed_root=paths.state_root,
            project_root=paths.project_root,
            final_kind="directory",
            require_final=True,
        )
    lock_path = paths.recovery_root / LOCK_NAME
    lock_path = _safe_path(
        lock_path,
        allowed_root=paths.recovery_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=read_only or os.path.lexists(lock_path),
    )
    handle = _open_lock_handle(lock_path, create=not read_only)
    acquired = False
    try:
        try:
            _acquire_os_lock(handle, initialize=not read_only)
        except OSError as error:
            raise RunnerError(
                "publication lock is already held or unavailable"
            ) from error
        acquired = True
        if not read_only:
            _recover_output_replacement(
                paths,
                paths.journal_path,
                allowed_root=paths.recovery_root,
            )
            for canonical_path in (paths.result_path, paths.report_path):
                _recover_output_replacement(
                    paths,
                    canonical_path,
                    allowed_root=paths.canonical_root,
                )
        yield
    finally:
        if acquired:
            try:
                _release_os_lock(handle)
            except OSError:
                pass
        try:
            handle.close()
        except OSError:
            pass


def _validate_pair_cell(value: Any, label: str, *, allow_absent: bool) -> dict[str, Any]:
    expected = {"present", "result_sha256", "report_sha256"}
    if not isinstance(value, dict) or set(value) != expected:
        raise RunnerError(f"invalid {label} pair fields")
    if type(value["present"]) is not bool:
        raise RunnerError(f"invalid {label} pair presence")
    if value["present"]:
        _validate_digest(value["result_sha256"], f"{label} result")
        _validate_digest(value["report_sha256"], f"{label} report")
    elif not allow_absent or (
        value["result_sha256"] is not None or value["report_sha256"] is not None
    ):
        raise RunnerError(f"invalid absent {label} pair")
    return dict(value)


def _validate_candidate_cell(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "result_sha256",
        "report_sha256",
    }:
        raise RunnerError("invalid candidate pair fields")
    _validate_digest(value["result_sha256"], "candidate result")
    _validate_digest(value["report_sha256"], "candidate report")
    return dict(value)


def _load_journal(
    paths: RunnerPaths,
    *,
    recover: bool = True,
) -> dict[str, Any]:
    if recover:
        _recover_output_replacement(
            paths,
            paths.journal_path,
            allowed_root=paths.recovery_root,
        )
    journal_path = _safe_path(
        paths.journal_path,
        allowed_root=paths.recovery_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    value = _load_json_object(journal_path, "publication journal")
    expected = {
        "schema_version",
        "transaction_id",
        "status",
        "receipt_name",
        "configuration_sha256",
        "previous_pair",
        "candidate_pair",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise RunnerError("invalid publication journal fields")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != TRANSACTION_SCHEMA_VERSION
    ):
        raise RunnerError("invalid publication journal schema")
    _validate_transaction_id(value["transaction_id"])
    if value["status"] not in {"awaiting_acceptance", "accepted"}:
        raise RunnerError("invalid publication journal status")
    _validate_receipt_name(value["receipt_name"])
    _validate_digest(value["configuration_sha256"], "journal configuration")
    _validate_pair_cell(value["previous_pair"], "previous", allow_absent=True)
    _validate_candidate_cell(value["candidate_pair"])
    for transaction_path in _transaction_paths(
        paths,
        value["transaction_id"],
    ).values():
        _safe_path(
            transaction_path,
            allowed_root=paths.recovery_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=os.path.lexists(transaction_path),
        )
    return value


def _receipt_from_transaction(transaction: Mapping[str, Any]) -> dict[str, Any]:
    previous = transaction["previous_pair"]
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "transaction_id": transaction["transaction_id"],
        "configuration_sha256": transaction["configuration_sha256"],
        "result_sha256": transaction["candidate_pair"]["result_sha256"],
        "report_sha256": transaction["candidate_pair"]["report_sha256"],
        "previous_pair_present": previous["present"],
        "previous_result_sha256": previous["result_sha256"],
        "previous_report_sha256": previous["report_sha256"],
    }


def _load_receipt(paths: RunnerPaths, receipt_path: Path) -> dict[str, Any]:
    receipt = _safe_path(
        receipt_path,
        allowed_root=paths.recovery_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    value = _load_json_object(receipt, "publication receipt")
    if set(value) != {
        "schema_version",
        "transaction_id",
        "configuration_sha256",
        "result_sha256",
        "report_sha256",
        "previous_pair_present",
        "previous_result_sha256",
        "previous_report_sha256",
    }:
        raise RunnerError("invalid publication receipt fields")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != RECEIPT_SCHEMA_VERSION
    ):
        raise RunnerError("invalid publication receipt schema")
    _validate_transaction_id(value["transaction_id"])
    for field in ("configuration_sha256", "result_sha256", "report_sha256"):
        _validate_digest(value[field], f"receipt {field}")
    if type(value["previous_pair_present"]) is not bool:
        raise RunnerError("invalid receipt previous-pair presence")
    if value["previous_pair_present"]:
        _validate_digest(value["previous_result_sha256"], "receipt previous result")
        _validate_digest(value["previous_report_sha256"], "receipt previous report")
    elif (
        value["previous_result_sha256"] is not None
        or value["previous_report_sha256"] is not None
    ):
        raise RunnerError("absent receipt previous pair cannot record hashes")
    return value


def _validate_receipt_matches(
    receipt: Mapping[str, Any],
    transaction: Mapping[str, Any],
) -> None:
    if dict(receipt) != _receipt_from_transaction(transaction):
        raise RunnerError("publication receipt does not match journal")


def _transaction_from_receipt(
    receipt_path: Path,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": TRANSACTION_SCHEMA_VERSION,
        "transaction_id": receipt["transaction_id"],
        "status": "awaiting_acceptance",
        "receipt_name": receipt_path.name,
        "configuration_sha256": receipt["configuration_sha256"],
        "previous_pair": {
            "present": receipt["previous_pair_present"],
            "result_sha256": receipt["previous_result_sha256"],
            "report_sha256": receipt["previous_report_sha256"],
        },
        "candidate_pair": {
            "result_sha256": receipt["result_sha256"],
            "report_sha256": receipt["report_sha256"],
        },
    }


def _reconstruct_rollback_transaction(
    paths: RunnerPaths,
    receipt_path: Path,
) -> dict[str, Any]:
    state = load_state(paths)
    if state["phase"] != "awaiting_acceptance":
        raise RunnerError("receipt rollback reconstruction requires awaiting state")
    receipt = _load_receipt(paths, receipt_path)
    transaction = _transaction_from_receipt(receipt_path, receipt)
    if (
        transaction["transaction_id"] != state["candidate_transaction_id"]
        or transaction["configuration_sha256"]
        != state["configuration_sha256"]
    ):
        raise RunnerError("receipt/state identity conflict; evidence retained")
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    for transaction_path in transaction_paths.values():
        _safe_path(
            transaction_path,
            allowed_root=paths.recovery_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=os.path.lexists(transaction_path),
        )
    allowed = {
        LOCK_NAME,
        receipt_path.name,
    }
    if os.path.lexists(paths.journal_path):
        allowed.add(JOURNAL_NAME)
    previous = transaction["previous_pair"]
    if previous["present"]:
        allowed.update(
            {
                transaction_paths["previous_result"].name,
                transaction_paths["previous_report"].name,
            }
        )
        for path, digest in (
            (transaction_paths["previous_result"], previous["result_sha256"]),
            (transaction_paths["previous_report"], previous["report_sha256"]),
        ):
            if not os.path.lexists(path) or _sha256_file(path) != digest:
                raise RunnerError(
                    "receipt rollback backup identity mismatch; evidence retained"
                )
    try:
        actual = {entry.name for entry in paths.recovery_root.iterdir()}
    except OSError as error:
        raise RunnerError("unable to inspect rollback recovery artifacts") from error
    if actual != allowed:
        raise RunnerError("rollback recovery artifacts conflict; evidence retained")
    return transaction


def _find_recovery_receipt(paths: RunnerPaths) -> Path:
    try:
        candidates = [
            entry
            for entry in paths.recovery_root.iterdir()
            if entry.name not in {JOURNAL_NAME, LOCK_NAME}
            and _RECEIPT_NAME_PATTERN.fullmatch(entry.name) is not None
        ]
    except OSError as error:
        raise RunnerError("unable to inspect recovery receipts") from error
    if len(candidates) != 1:
        raise RunnerError("rollback recovery requires exactly one receipt")
    return candidates[0]


def _persist_journal(paths: RunnerPaths, transaction: Mapping[str, Any]) -> None:
    if os.path.lexists(paths.journal_path):
        raise RunnerError("a publication journal is already active")
    _write_new_fsynced(paths.journal_path, canonical_json_bytes(dict(transaction)))
    if _load_journal(paths) != dict(transaction):
        raise RunnerError("publication journal readback mismatch")


def _replace_journal(paths: RunnerPaths, transaction: Mapping[str, Any]) -> None:
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    update = transaction_paths["journal_update"]
    _durable_unlink(update)
    _write_new_fsynced(update, canonical_json_bytes(dict(transaction)))
    _replace_entry_durably(update, paths.journal_path)
    if _load_journal(paths) != dict(transaction):
        raise RunnerError("publication journal update mismatch")


def _cleanup_transaction(
    paths: RunnerPaths,
    transaction: Mapping[str, Any],
) -> None:
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    for path in transaction_paths.values():
        _durable_unlink(path)
    _durable_unlink(paths.receipt_path(transaction["receipt_name"]))
    _durable_unlink(paths.journal_path)


def _discard_unjournaled(paths: RunnerPaths, transaction_id: str) -> None:
    for path in _transaction_paths(paths, transaction_id).values():
        try:
            _durable_unlink(path)
        except OSError:
            pass


def _validate_candidate_pair(
    paths: RunnerPaths,
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_canonical_pair_metadata(paths, require_entries=True)
    try:
        result_bytes = _read_file_nofollow(paths.result_path)
        report_bytes = _read_file_nofollow(paths.report_path)
    except OSError as error:
        raise RunnerError("unable to read candidate canonical pair") from error
    candidate = transaction["candidate_pair"]
    if _sha256_bytes(result_bytes) != candidate["result_sha256"]:
        raise RunnerError("candidate result digest mismatch")
    if _sha256_bytes(report_bytes) != candidate["report_sha256"]:
        raise RunnerError("candidate report digest mismatch")
    try:
        payload = json.loads(result_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RunnerError("candidate result is not valid JSON") from error
    try:
        validated = validate_phase_b_result(payload)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"candidate result is invalid: {error}") from error
    if canonical_json_bytes(validated) != result_bytes:
        raise RunnerError("candidate result bytes are not deterministic")
    expected_report = render_report(validated, candidate["result_sha256"]).encode(
        "utf-8"
    )
    if expected_report != report_bytes:
        raise RunnerError("candidate report is not a deterministic readback")
    return validated


def _canonical_pair_matches(
    paths: RunnerPaths,
    *,
    result_sha256: str,
    report_sha256: str,
) -> bool:
    _validate_canonical_pair_metadata(
        paths,
        require_entries=False,
        allow_partial=True,
    )
    if not (
        os.path.lexists(paths.result_path)
        and os.path.lexists(paths.report_path)
    ):
        return False
    return (
        _sha256_file(paths.result_path) == result_sha256
        and _sha256_file(paths.report_path) == report_sha256
    )


def _restore_transaction(
    paths: RunnerPaths,
    transaction: Mapping[str, Any],
    *,
    update_state: bool,
) -> str:
    state = load_state(paths)
    if update_state:
        if (
            state["phase"] not in {"awaiting_acceptance", "rejected"}
            or state["candidate_transaction_id"] != transaction["transaction_id"]
        ):
            raise RunnerError(
                "rollback identity does not match runner state; evidence retained"
            )
    elif state["phase"] != "lockbox_complete":
        raise RunnerError(
            "pre-awaiting rollback requires lockbox-complete state; evidence retained"
        )
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    previous = transaction["previous_pair"]
    candidate = transaction["candidate_pair"]
    _validate_canonical_pair_metadata(
        paths,
        require_entries=False,
        allow_partial=True,
    )
    if previous["present"]:
        if not _canonical_pair_matches(
            paths,
            result_sha256=previous["result_sha256"],
            report_sha256=previous["report_sha256"],
        ):
            try:
                previous_result = _read_file_nofollow(
                    transaction_paths["previous_result"]
                )
                previous_report = _read_file_nofollow(
                    transaction_paths["previous_report"]
                )
            except OSError as error:
                raise RunnerError("required previous-pair backup is missing") from error
            if _sha256_bytes(previous_result) != previous["result_sha256"]:
                raise RunnerError("previous result backup digest mismatch")
            if _sha256_bytes(previous_report) != previous["report_sha256"]:
                raise RunnerError("previous report backup digest mismatch")
            for key in ("restore_result", "restore_report"):
                _durable_unlink(transaction_paths[key])
            _write_new_fsynced(
                transaction_paths["restore_result"],
                previous_result,
            )
            _write_new_fsynced(
                transaction_paths["restore_report"],
                previous_report,
            )
            _validate_canonical_pair_metadata(
                paths,
                require_entries=False,
                allow_partial=True,
            )
            _ensure_directory_durable(Path(paths.canonical_root))
            _validate_canonical_pair_metadata(
                paths,
                require_entries=False,
                allow_partial=True,
            )
            _replace_entry_durably(
                transaction_paths["restore_result"],
                paths.result_path,
            )
            _replace_entry_durably(
                transaction_paths["restore_report"],
                paths.report_path,
            )
            if not _canonical_pair_matches(
                paths,
                result_sha256=previous["result_sha256"],
                report_sha256=previous["report_sha256"],
            ):
                raise RunnerError("restored previous pair digest mismatch")
    else:
        for path, digest, label in (
            (paths.result_path, candidate["result_sha256"], "result"),
            (paths.report_path, candidate["report_sha256"], "report"),
        ):
            if os.path.lexists(path) and _sha256_file(path) != digest:
                raise RunnerError(
                    f"cannot restore absent previous pair over unexpected {label}"
                )
        _durable_unlink(paths.result_path)
        _durable_unlink(paths.report_path)
    if update_state:
        if state["phase"] == "awaiting_acceptance":
            _transition(paths, state, "rejected")
        elif state["phase"] != "rejected":
            raise RunnerError("recovery state does not match publication journal")
    _cleanup_transaction(paths, transaction)
    return "restored"


def _recover_locked(paths: RunnerPaths) -> str:
    if not os.path.lexists(paths.journal_path):
        state = load_state(paths)
        if state["phase"] == "lockbox_complete":
            try:
                debris = [
                    entry
                    for entry in paths.recovery_root.iterdir()
                    if entry.name != LOCK_NAME
                ]
            except OSError as error:
                raise RunnerError("unable to inspect unjournaled recovery state") from error
            if not debris:
                return "none"
            if any(
                _UNJOURNALED_NAME_PATTERN.fullmatch(entry.name) is None
                for entry in debris
            ):
                raise RunnerError(
                    "unidentified unjournaled recovery evidence is retained"
                )
            for entry in debris:
                _durable_unlink(entry)
            return "discarded_unjournaled"
        if state["phase"] != "awaiting_acceptance":
            return "none"
        receipt_path = _find_recovery_receipt(paths)
        transaction = _reconstruct_rollback_transaction(paths, receipt_path)
        return _restore_transaction(paths, transaction, update_state=True)
    try:
        transaction = _load_journal(paths)
    except RunnerError:
        state = load_state(paths)
        if state["phase"] != "awaiting_acceptance":
            raise
        receipt_path = _find_recovery_receipt(paths)
        transaction = _reconstruct_rollback_transaction(paths, receipt_path)
        return _restore_transaction(paths, transaction, update_state=True)
    state = load_state(paths)
    if (
        state["phase"] in {"awaiting_acceptance", "accepted", "rejected"}
        and state["candidate_transaction_id"] != transaction["transaction_id"]
    ):
        raise RunnerError("publication journal identity does not match runner state")
    if transaction["status"] == "accepted":
        _validate_candidate_pair(paths, transaction)
        if state["phase"] == "awaiting_acceptance":
            _transition(paths, state, "accepted")
        elif state["phase"] != "accepted":
            raise RunnerError("accepted journal does not match runner state")
        _cleanup_transaction(paths, transaction)
        return "accepted"
    update_state = state["phase"] in {"awaiting_acceptance", "rejected"}
    if state["phase"] not in {
        "lockbox_complete",
        "awaiting_acceptance",
        "rejected",
    }:
        raise RunnerError("publication journal does not match runner state")
    return _restore_transaction(paths, transaction, update_state=update_state)


def recover_publication(paths: RunnerPaths) -> str:
    with publication_lock(paths):
        return _recover_locked(paths)


def stage_candidate(
    paths: RunnerPaths,
    receipt_name: str,
) -> dict[str, Any]:
    receipt_name = _validate_receipt_name(receipt_name)
    with publication_lock(paths):
        recovery = _recover_locked(paths)
        state = load_state(paths)
        if recovery == "restored" and state["phase"] == "rejected":
            raise RunnerError("awaiting candidate was recovered as rejected")
        _require_phase(state, "lockbox_complete")
        _revalidate_bound_preflight(paths, state)
        _validate_canonical_pair_metadata(paths, require_entries=False)
        receipt_path = paths.receipt_path(receipt_name)
        _safe_path(
            receipt_path,
            allowed_root=paths.recovery_root,
            project_root=paths.project_root,
        )
        if os.path.lexists(receipt_path):
            raise RunnerError("publication receipt already exists")

        result = build_aggregate_result(paths)
        result_bytes = canonical_json_bytes(result)
        result_sha256 = _sha256_bytes(result_bytes)
        report_bytes = render_report(result, result_sha256).encode("utf-8")
        report_sha256 = _sha256_bytes(report_bytes)
        transaction_id = uuid.uuid4().hex
        transaction_paths = _transaction_paths(paths, transaction_id)
        journal_durable = False
        try:
            _write_new_fsynced(transaction_paths["new_result"], result_bytes)
            _write_new_fsynced(transaction_paths["new_report"], report_bytes)
            if (
                _read_file_nofollow(transaction_paths["new_result"]) != result_bytes
                or _read_file_nofollow(transaction_paths["new_report"])
                != report_bytes
            ):
                raise RunnerError("staged candidate readback mismatch")
            result_exists = os.path.lexists(paths.result_path)
            report_exists = os.path.lexists(paths.report_path)
            if result_exists != report_exists:
                raise RunnerError("partial canonical pair")
            previous_result_sha256: str | None = None
            previous_report_sha256: str | None = None
            if result_exists:
                previous_result = _read_file_nofollow(paths.result_path)
                previous_report = _read_file_nofollow(paths.report_path)
                previous_result_sha256 = _sha256_bytes(previous_result)
                previous_report_sha256 = _sha256_bytes(previous_report)
                _write_new_fsynced(
                    transaction_paths["previous_result"],
                    previous_result,
                )
                _write_new_fsynced(
                    transaction_paths["previous_report"],
                    previous_report,
                )
            transaction = {
                "schema_version": TRANSACTION_SCHEMA_VERSION,
                "transaction_id": transaction_id,
                "status": "awaiting_acceptance",
                "receipt_name": receipt_name,
                "configuration_sha256": state["configuration_sha256"],
                "previous_pair": {
                    "present": result_exists,
                    "result_sha256": previous_result_sha256,
                    "report_sha256": previous_report_sha256,
                },
                "candidate_pair": {
                    "result_sha256": result_sha256,
                    "report_sha256": report_sha256,
                },
            }
            _persist_journal(paths, transaction)
            journal_durable = True
            _validate_canonical_pair_metadata(paths, require_entries=False)
            _ensure_directory_durable(Path(paths.canonical_root))
            _validate_canonical_pair_metadata(paths, require_entries=False)
            _replace_entry_durably(
                transaction_paths["new_result"],
                paths.result_path,
            )
            _replace_entry_durably(
                transaction_paths["new_report"],
                paths.report_path,
            )
            _validate_candidate_pair(paths, transaction)
            receipt = _receipt_from_transaction(transaction)
            _write_new_fsynced(receipt_path, canonical_json_bytes(receipt))
            if _load_receipt(paths, receipt_path) != receipt:
                raise RunnerError("publication receipt readback mismatch")
            _revalidate_bound_preflight(paths, state)
            _validated_packet(paths, state, require_bound=True)
            if _sha256_file(_validate_lockbox_path(paths)) != state[
                "lockbox_result_sha256"
            ]:
                raise RunnerError("lockbox result changed before awaiting transition")
            _validate_candidate_pair(paths, transaction)
            _transition(
                paths,
                state,
                "awaiting_acceptance",
                candidate_transaction_id=transaction_id,
            )
            return receipt
        except Exception as error:
            if journal_durable:
                try:
                    current_state = load_state(paths)
                    if (
                        current_state["phase"] == "awaiting_acceptance"
                        and current_state["candidate_transaction_id"]
                        == transaction_id
                    ):
                        update_state = True
                    elif current_state["phase"] == "lockbox_complete":
                        update_state = False
                    else:
                        raise RunnerError(
                            "staging failure state identity conflicts; evidence retained"
                        )
                    _restore_transaction(
                        paths,
                        transaction,
                        update_state=update_state,
                    )
                except Exception as restore_error:
                    raise RunnerError(
                        "candidate staging failed and previous-pair restoration failed"
                    ) from restore_error
                raise RunnerError(
                    "candidate staging failed; previous pair restored"
                ) from error
            _discard_unjournaled(paths, transaction_id)
            if isinstance(error, RunnerError):
                raise
            raise RunnerError("candidate staging failed before publication") from error


def _load_matching_transaction_and_receipt(
    paths: RunnerPaths,
    receipt_path: Path,
    *,
    transaction: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if transaction is None:
        transaction = _load_journal(paths)
    expected_path = paths.receipt_path(transaction["receipt_name"])
    supplied = _safe_path(
        receipt_path,
        allowed_root=paths.recovery_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    if supplied != expected_path:
        raise RunnerError("receipt path does not match publication journal")
    receipt = _load_receipt(paths, supplied)
    _validate_receipt_matches(receipt, transaction)
    return transaction, receipt


def accept_receipt(paths: RunnerPaths, receipt_path: Path) -> None:
    with publication_lock(paths):
        state = load_state(paths)
        _require_phase(state, "awaiting_acceptance")
        transaction: dict[str, Any] | None = None
        identity_validated = False
        try:
            transaction = _load_journal(paths)
            transaction, _receipt = _load_matching_transaction_and_receipt(
                paths,
                Path(receipt_path),
                transaction=transaction,
            )
            if transaction["status"] != "awaiting_acceptance":
                raise RunnerError("publication transaction is not awaiting acceptance")
            if transaction["transaction_id"] != state["candidate_transaction_id"]:
                raise RunnerError("journal identity does not match runner state")
            if (
                transaction["configuration_sha256"]
                != state["configuration_sha256"]
            ):
                raise RunnerError("journal configuration does not match runner state")
            identity_validated = True
            _config, _split, _ledger, digests = _validate_bound_preflight_inputs(paths)
            for field, digest in digests.items():
                if state[field] != digest:
                    label = field.removesuffix("_sha256").replace("_", " ")
                    raise RunnerError(f"{label} changed after preflight")
            _validate_candidate_pair(paths, transaction)
        except RunnerError as error:
            if transaction is not None and identity_validated:
                try:
                    _restore_transaction(paths, transaction, update_state=True)
                except Exception as restore_error:
                    raise RunnerError(
                        "acceptance failed and previous-pair restoration failed"
                    ) from restore_error
            raise
        transaction["status"] = "accepted"
        _replace_journal(paths, transaction)
        _transition(paths, state, "accepted")
        _cleanup_transaction(paths, transaction)


def reject_receipt(paths: RunnerPaths, receipt_path: Path) -> None:
    with publication_lock(paths):
        state = load_state(paths)
        _require_phase(state, "awaiting_acceptance")
        try:
            transaction = _load_journal(paths)
        except RunnerError:
            transaction = _reconstruct_rollback_transaction(
                paths,
                Path(receipt_path),
            )
            _restore_transaction(paths, transaction, update_state=True)
            return
        transaction, _receipt = _load_matching_transaction_and_receipt(
            paths,
            Path(receipt_path),
            transaction=transaction,
        )
        if transaction["status"] != "awaiting_acceptance":
            raise RunnerError("accepted publication cannot be rejected")
        if transaction["transaction_id"] != state["candidate_transaction_id"]:
            raise RunnerError("journal identity does not match runner state")
        _restore_transaction(paths, transaction, update_state=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guard EMOTION-STATE-002 Phase B synthetic/offline phases."
    )
    parser.add_argument(
        "phase",
        choices=(
            "preflight",
            "non-lockbox",
            "lockbox",
            "stage-candidate",
            "accept-receipt",
            "reject-receipt",
        ),
    )
    parser.add_argument("--receipt")
    parsed = parser.parse_args(argv)
    needs_receipt = parsed.phase in {
        "stage-candidate",
        "accept-receipt",
        "reject-receipt",
    }
    if needs_receipt != (parsed.receipt is not None):
        parser.error("--receipt is required only for publication receipt phases")
    return parsed


def _paths_from_args(arguments: argparse.Namespace) -> RunnerPaths:
    del arguments
    return RunnerPaths.production()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    paths = _paths_from_args(arguments)
    try:
        if arguments.phase == "preflight":
            state = run_preflight(paths)
            output: Any = state
        elif arguments.phase == "non-lockbox":
            output = run_non_lockbox(paths)
        elif arguments.phase == "lockbox":
            output = run_lockbox(paths)
        elif arguments.phase == "stage-candidate":
            output = stage_candidate(paths, arguments.receipt)
        elif arguments.phase == "accept-receipt":
            receipt_path = paths.receipt_path(arguments.receipt)
            accept_receipt(paths, receipt_path)
            output = load_state(paths)
        else:
            receipt_path = paths.receipt_path(arguments.receipt)
            reject_receipt(paths, receipt_path)
            output = load_state(paths)
    except RunnerError as error:
        print(f"EMOTION-STATE-002 Phase B runner failed: {error}", file=sys.stderr)
        return 1
    print(canonical_json_bytes(output).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
