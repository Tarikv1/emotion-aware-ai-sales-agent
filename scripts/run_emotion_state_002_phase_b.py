#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

if os.name == "nt":
    import msvcrt
else:
    import fcntl


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_emotion_state_002_phase_b import (
    EXPECTED_VALIDITY,
    EXPECTED_STATIC_FILE_SHA256,
    derive_phase_b_decision,
    serialized_decision_evidence_mint_sha256,
    validate_config,
    validate_decision_inputs,
    validate_environment_lock,
    validate_feature_schema,
    validate_lockbox_ami_input,
    validate_lockbox_lineage,
    validate_lockbox_result,
    validate_non_lockbox_packet,
    validate_phase_b_input_ledger,
    validate_phase_b_result,
    validate_phase_b_split_manifest,
    validate_split_schema,
    validated_lockbox_summary,
)


STATE_SCHEMA_VERSION = 1
TRANSACTION_SCHEMA_VERSION = 1
RECEIPT_SCHEMA_VERSION = 1
JOURNAL_NAME = "transaction.json"
LOCK_NAME = "publication.lock"
LOCKBOX_LOCK_NAME = "lockbox.lock"
LOCKBOX_RESERVATION_NAME = "lockbox-reservation.json"
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
class _DirectoryAuthority:
    path: Path
    posix_descriptor: int | None = None
    windows_handle: int | None = None


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
    lockbox_result_path: Path
    authority: str = "invalid"

    @classmethod
    def production(cls) -> "RunnerPaths":
        root = ROOT
        state_root = root / ".tmp" / "emotion-state-002-phase-b"
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
                / "emotion_state_phase_b_feature_v1.schema.json"
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
            lockbox_result_path=state_root / "lockbox" / "lockbox-result.json",
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
            authority="injected-test",
        )

    @property
    def state_path(self) -> Path:
        return Path(self.state_root) / "state.json"

    @property
    def non_lockbox_root(self) -> Path:
        return Path(self.state_root) / "non-lockbox"

    @property
    def lockbox_root(self) -> Path:
        return Path(self.state_root) / "lockbox"

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


def _read_file_nofollow(path: Path, *, maximum_bytes: int = 16_777_216) -> bytes:
    """Read a regular file through a no-follow handle and bind its identity."""
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
            ):
                os.close(descriptor)
                raise RunnerError("bound input is not a regular no-follow file")
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
        ):
            raise RunnerError("bound file changed while being read")
        return content
    except OSError as error:
        raise RunnerError(f"unable to read bound file: {Path(path).name}") from error
    finally:
        os.close(descriptor)


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
            "lockbox_result_path",
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


def _validate_lockbox_path(paths: RunnerPaths) -> Path:
    try:
        return _safe_path(
            paths.lockbox_result_path,
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
        0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
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
    destination_digest = (
        _sha256_file(destination) if destination_exists else None
    )
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
            _durable_unlink(prior_path, missing_ok=False)
            _durable_unlink(intent_path, missing_ok=False)
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
            raise RunnerError("restored durable replacement prior digest mismatch")
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
    _durable_unlink(intent_path, missing_ok=False)
    return outcome


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


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"duplicate JSON key: {key}")
                value[key] = item
            return value

        payload = json.loads(
            _read_file_nofollow(path).decode("utf-8"),
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


def load_state(paths: RunnerPaths) -> dict[str, Any]:
    _validate_layout(paths)
    state_path = _safe_path(
        paths.state_path,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=False,
    )
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


def _assert_closed_environment() -> None:
    credentials = _forbidden_credentials()
    if credentials:
        raise RunnerError(
            "credential environment variables are blocked: "
            + ", ".join(credentials)
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


def _validate_preflight_inputs(
    paths: RunnerPaths,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    _validate_layout(paths)
    config_path = _validate_input_path(paths, paths.config_path)
    environment_path = _validate_input_path(paths, paths.environment_lock_path)
    feature_path = _validate_input_path(paths, paths.feature_schema_path)
    split_schema_path = _validate_input_path(paths, paths.split_schema_path)
    split_path = _validate_input_path(paths, paths.split_manifest_path)
    ledger_path = _validate_input_path(paths, paths.input_ledger_path)
    try:
        config = validate_config(_load_json_object(config_path, "configuration"))
        validate_environment_lock(
            _load_json_object(environment_path, "environment lock")
        )
        validate_feature_schema(_load_json_object(feature_path, "feature schema"))
        validate_split_schema(
            _load_json_object(split_schema_path, "split schema")
        )
        split = validate_phase_b_split_manifest(
            _load_json_object(split_path, "split manifest")
        )
        ledger = validate_phase_b_input_ledger(
            _load_json_object(ledger_path, "input ledger")
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"preflight validation failed: {error}") from error
    static_checks = {
        "configuration_sha256": _sha256_file(config_path),
        "environment_lock_sha256": _sha256_file(environment_path),
        "feature_schema_sha256": _sha256_file(feature_path),
        "split_schema_sha256": _sha256_file(split_schema_path),
    }
    for field, digest in EXPECTED_STATIC_FILE_SHA256.items():
        if static_checks[field] != digest:
            label = field.removesuffix("_sha256").replace("_", " ")
            raise RunnerError(
                f"{label} tracked bytes do not match the frozen identity"
            )
    return config, split, ledger, {
        "configuration_sha256": static_checks["configuration_sha256"],
        "environment_lock_sha256": static_checks["environment_lock_sha256"],
        "input_ledger_sha256": _sha256_file(ledger_path),
        "split_manifest_sha256": _sha256_file(split_path),
    }


def run_preflight(paths: RunnerPaths) -> dict[str, Any]:
    _assert_closed_environment()
    _config, _split, _ledger, digests = _validate_preflight_inputs(paths)
    state_exists = os.path.lexists(paths.state_path)
    state = load_state(paths) if state_exists else _initial_state()
    _require_phase(state, "initialized")
    _ensure_directory_durable(Path(paths.state_root))
    return _transition(
        paths,
        state,
        "preflight_complete",
        **digests,
        non_lockbox_packet_sha256=UNSET_DIGEST,
        lockbox_result_sha256=UNSET_DIGEST,
        lockbox_decision_evidence_sha256=UNSET_DIGEST,
        lockbox_decision_evidence_mint_sha256=UNSET_DIGEST,
    )


def _assert_anchor_digests(paths: RunnerPaths, state: Mapping[str, Any]) -> None:
    checks = (
        ("configuration", paths.config_path, state["configuration_sha256"]),
        (
            "environment",
            paths.environment_lock_path,
            state["environment_lock_sha256"],
        ),
        ("input ledger", paths.input_ledger_path, state["input_ledger_sha256"]),
        ("split manifest", paths.split_manifest_path, state["split_manifest_sha256"]),
    )
    for label, path, expected in checks:
        _validate_input_path(paths, path)
        if _sha256_file(path) != expected:
            raise RunnerError(f"{label} changed after preflight")


def _revalidate_bound_preflight(
    paths: RunnerPaths,
    state: Mapping[str, Any],
) -> None:
    _assert_anchor_digests(paths, state)
    _config, _split, _ledger, digests = _validate_preflight_inputs(paths)
    if any(digests[field] != state[field] for field in digests):
        raise RunnerError("preflight anchor changed after validation")


def _validated_packet(
    paths: RunnerPaths,
    state: Mapping[str, Any],
    *,
    require_bound: bool,
) -> tuple[dict[str, Any], str]:
    packet_path = _validate_non_lockbox_path(paths)
    digest_before = _sha256_file(packet_path)
    packet = _load_json_object(packet_path, "non-lockbox packet")
    try:
        validated = validate_non_lockbox_packet(packet)
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid non-lockbox packet: {error}") from error
    digest = _sha256_file(packet_path)
    if digest != digest_before:
        raise RunnerError("non-lockbox packet changed during semantic validation")
    if require_bound and digest != state["non_lockbox_packet_sha256"]:
        raise RunnerError("non-lockbox packet changed after validation")
    return validated, digest


def run_non_lockbox(paths: RunnerPaths) -> dict[str, Any]:
    _assert_closed_environment()
    state = load_state(paths)
    _require_phase(state, "preflight_complete")
    _revalidate_bound_preflight(paths, state)
    _packet, packet_digest = _validated_packet(paths, state, require_bound=False)
    _revalidate_bound_preflight(paths, state)
    _packet, second_digest = _validated_packet(paths, state, require_bound=False)
    _assert_closed_environment()
    if second_digest != packet_digest:
        raise RunnerError("non-lockbox packet changed during validation")
    return _transition(
        paths,
        state,
        "non_lockbox_complete",
        non_lockbox_packet_sha256=packet_digest,
    )


def _open_lock_handle(path: Path) -> BinaryIO:
    _require_mutation_path_proof(path)
    if not os.path.lexists(path):
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
            paths.lockbox_result_path,
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


def _load_reservation(paths: RunnerPaths) -> dict[str, Any]:
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


def build_aggregate_result(paths: RunnerPaths) -> dict[str, Any]:
    state = load_state(paths)
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
    split_path = _validate_input_path(paths, paths.split_manifest_path)
    ledger_path = _validate_input_path(paths, paths.input_ledger_path)
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
    reservation = _load_reservation(paths)
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
        "raw_csv_sha256": ledger["raw_csv_sha256"],
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


def _acquire_os_lock(handle: BinaryIO) -> None:
    if os.name == "nt":
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
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
def publication_lock(paths: RunnerPaths) -> Iterator[None]:
    _validate_layout(paths)
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
        require_final=os.path.lexists(lock_path),
    )
    handle = _open_lock_handle(lock_path)
    acquired = False
    try:
        try:
            _acquire_os_lock(handle)
        except OSError as error:
            raise RunnerError(
                "publication lock is already held or unavailable"
            ) from error
        acquired = True
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


def _load_journal(paths: RunnerPaths) -> dict[str, Any]:
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
            if _sha256_file(paths.lockbox_result_path) != state[
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
            _config, _split, _ledger, digests = _validate_preflight_inputs(paths)
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
