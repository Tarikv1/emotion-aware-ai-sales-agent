#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, BinaryIO
from unittest.mock import patch

if os.name == "nt":
    import msvcrt
else:
    import fcntl


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_emotion_state_002_phase_b import (
    load_json_strict,
    validate_config,
    validate_environment_lock,
    validate_feature_schema,
    validate_lockbox_result,
    validate_non_lockbox_packet,
    validate_phase_b_input_ledger,
    validate_phase_b_result,
    validate_split_schema,
)


STATE_SCHEMA_VERSION = 1
TRANSACTION_SCHEMA_VERSION = 1
RECEIPT_SCHEMA_VERSION = 1
JOURNAL_NAME = "transaction.json"
LOCK_NAME = "publication.lock"
UNSET_DIGEST = "0" * 64
PRIVATE_COMPONENTS = frozenset(
    {"private", "private-restricted", "secrets", ".secrets"}
)
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
)
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_TRANSACTION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_RECEIPT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")


class RunnerError(RuntimeError):
    """A fail-closed Phase B runner or publication error."""


@dataclass(frozen=True)
class RunnerPaths:
    project_root: Path
    input_root: Path
    state_root: Path
    canonical_root: Path
    config_path: Path
    environment_lock_path: Path
    feature_schema_path: Path
    split_manifest_path: Path
    input_ledger_path: Path
    non_lockbox_packet_path: Path
    lockbox_result_path: Path

    @classmethod
    def from_project_root(cls, project_root: Path = ROOT) -> "RunnerPaths":
        root = Path(project_root)
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
            split_manifest_path=(
                root
                / "research"
                / "sources"
                / "emotion_state"
                / "emotion_state_evaluation_split_v1.schema.json"
            ),
            input_ledger_path=state_root / "inputs" / "input-ledger.json",
            non_lockbox_packet_path=(
                state_root / "non-lockbox" / "non-lockbox-packet.json"
            ),
            lockbox_result_path=state_root / "lockbox" / "lockbox-result.json",
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


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as error:
        raise RunnerError(f"unable to read bound file: {path.name}") from error


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
    return candidate


def _validate_layout(paths: RunnerPaths) -> None:
    project = _absolute_lexical(Path(paths.project_root), Path(paths.project_root))
    input_root = _absolute_lexical(Path(paths.input_root), project)
    state_root = _absolute_lexical(Path(paths.state_root), project)
    canonical_root = _absolute_lexical(Path(paths.canonical_root), project)
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


def _write_new_fsynced(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        raise RunnerError(f"unable to durably write {path.name}") from error


def _replace_bytes_durably(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        _write_new_fsynced(temporary, content)
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
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
            ):
                raise RunnerError(
                    "preflight state must retain unopened artifact placeholders"
                )
        elif phase == "non_lockbox_complete":
            if (
                payload["non_lockbox_packet_sha256"] == UNSET_DIGEST
                or payload["lockbox_result_sha256"] != UNSET_DIGEST
            ):
                raise RunnerError(
                    "non-lockbox state artifact digests do not match its phase"
                )
        elif (
            payload["non_lockbox_packet_sha256"] == UNSET_DIGEST
            or payload["lockbox_result_sha256"] == UNSET_DIGEST
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
        payload = load_json_strict(path)
    except (OSError, ValueError) as error:
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
    Path(paths.state_root).mkdir(parents=True, exist_ok=True)
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


def _blocked_network(*_args: Any, **_kwargs: Any) -> None:
    raise RunnerError("network access is blocked during Phase B evaluation")


@contextmanager
def _offline_operation_boundary() -> Iterator[None]:
    _assert_closed_environment()
    import socket

    with (
        patch.object(socket, "create_connection", _blocked_network),
        patch.object(socket.socket, "connect", _blocked_network),
        patch.object(socket.socket, "connect_ex", _blocked_network),
        patch.object(socket.socket, "sendto", _blocked_network),
    ):
        yield


def _validate_preflight_inputs(
    paths: RunnerPaths,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    _validate_layout(paths)
    config_path = _validate_input_path(paths, paths.config_path)
    environment_path = _validate_input_path(paths, paths.environment_lock_path)
    feature_path = _validate_input_path(paths, paths.feature_schema_path)
    split_path = _validate_input_path(paths, paths.split_manifest_path)
    ledger_path = _validate_input_path(paths, paths.input_ledger_path)
    try:
        config = validate_config(_load_json_object(config_path, "configuration"))
        validate_environment_lock(
            _load_json_object(environment_path, "environment lock")
        )
        validate_feature_schema(_load_json_object(feature_path, "feature schema"))
        split = validate_split_schema(
            _load_json_object(split_path, "split manifest")
        )
        ledger = validate_phase_b_input_ledger(
            _load_json_object(ledger_path, "input ledger")
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"preflight validation failed: {error}") from error
    return config, split, ledger, {
        "configuration_sha256": _sha256_file(config_path),
        "environment_lock_sha256": _sha256_file(environment_path),
        "input_ledger_sha256": _sha256_file(ledger_path),
        "split_manifest_sha256": _sha256_file(split_path),
    }


def run_preflight(paths: RunnerPaths) -> dict[str, Any]:
    _assert_closed_environment()
    _config, _split, _ledger, digests = _validate_preflight_inputs(paths)
    state_exists = os.path.lexists(paths.state_path)
    state = load_state(paths) if state_exists else _initial_state()
    _require_phase(state, "initialized")
    Path(paths.state_root).mkdir(parents=True, exist_ok=True)
    return _transition(
        paths,
        state,
        "preflight_complete",
        **digests,
        non_lockbox_packet_sha256=UNSET_DIGEST,
        lockbox_result_sha256=UNSET_DIGEST,
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


def run_non_lockbox(
    paths: RunnerPaths,
    *,
    operation: Callable[[], None] | None = None,
) -> dict[str, Any]:
    state = load_state(paths)
    _require_phase(state, "preflight_complete")
    _assert_anchor_digests(paths, state)
    packet_path = _validate_non_lockbox_path(paths)
    try:
        with _offline_operation_boundary():
            if operation is not None:
                operation()
            _assert_closed_environment()
            packet = _load_json_object(packet_path, "non-lockbox packet")
            validate_non_lockbox_packet(packet)
    except RunnerError:
        raise
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid non-lockbox packet: {error}") from error
    return _transition(
        paths,
        state,
        "non_lockbox_complete",
        non_lockbox_packet_sha256=_sha256_file(packet_path),
    )


def run_lockbox(
    paths: RunnerPaths,
    *,
    operation: Callable[[], None] | None = None,
) -> dict[str, Any]:
    state = load_state(paths)
    _require_phase(state, "non_lockbox_complete")
    if state["lockbox_open_count"] != 0:
        raise RunnerError("final lockbox has already been opened")
    _assert_anchor_digests(paths, state)
    packet_path = _validate_non_lockbox_path(paths)
    if _sha256_file(packet_path) != state["non_lockbox_packet_sha256"]:
        raise RunnerError("non-lockbox packet changed before lockbox")
    lockbox_path = _validate_lockbox_path(paths)
    try:
        with _offline_operation_boundary():
            if operation is not None:
                operation()
            _assert_closed_environment()
            lockbox_result = _load_json_object(lockbox_path, "lockbox result")
            validate_lockbox_result(lockbox_result)
    except RunnerError:
        raise
    except (TypeError, ValueError) as error:
        raise RunnerError(f"invalid lockbox result: {error}") from error
    return _transition(
        paths,
        state,
        "lockbox_complete",
        lockbox_open_count=1,
        lockbox_result_sha256=_sha256_file(lockbox_path),
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
    _assert_anchor_digests(paths, state)
    config_path = _validate_input_path(paths, paths.config_path)
    feature_path = _validate_input_path(paths, paths.feature_schema_path)
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
        ledger = validate_phase_b_input_ledger(
            _load_json_object(ledger_path, "input ledger")
        )
        packet = validate_non_lockbox_packet(
            _load_json_object(packet_path, "non-lockbox packet")
        )
        lockbox = validate_lockbox_result(
            _load_json_object(lockbox_path, "lockbox result")
        )
    except (TypeError, ValueError) as error:
        raise RunnerError(f"aggregate input validation failed: {error}") from error
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
        "split_manifest_sha256": state["split_manifest_sha256"],
        "label_aggregates": ledger["label_aggregates"],
        "model_settings": packet["model_settings"],
        "metric_definitions": packet["metric_definitions"],
        "non_lockbox_review_sha256": packet["review_sha256"],
        "lockbox": {
            "open_count": state["lockbox_open_count"],
            "crema": lockbox["crema"],
            "ami": lockbox["ami"],
        },
        "decision": lockbox["decision"],
        "closed_boundaries": config["boundaries"],
    }
    del feature
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
    Path(paths.recovery_root).mkdir(parents=True, exist_ok=True)
    _safe_path(
        paths.recovery_root,
        allowed_root=paths.state_root,
        project_root=paths.project_root,
        final_kind="directory",
        require_final=True,
    )
    lock_path = paths.recovery_root / LOCK_NAME
    if os.path.lexists(lock_path):
        _safe_path(
            lock_path,
            allowed_root=paths.recovery_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
    try:
        handle = lock_path.open("a+b")
    except OSError as error:
        raise RunnerError("unable to open publication lock") from error
    acquired = False
    try:
        inspected_lock = _safe_path(
            lock_path,
            allowed_root=paths.recovery_root,
            project_root=paths.project_root,
            final_kind="file",
            require_final=True,
        )
        lock_status = os.lstat(inspected_lock)
        handle_status = os.fstat(handle.fileno())
        if (
            getattr(lock_status, "st_dev", None)
            != getattr(handle_status, "st_dev", None)
            or getattr(lock_status, "st_ino", None)
            != getattr(handle_status, "st_ino", None)
        ):
            raise RunnerError("publication lock entry changed during open")
        try:
            _acquire_os_lock(handle)
        except OSError as error:
            raise RunnerError(
                "publication lock is already held or unavailable"
            ) from error
        acquired = True
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
    journal_path = _safe_path(
        paths.journal_path,
        allowed_root=paths.recovery_root,
        project_root=paths.project_root,
        final_kind="file",
        require_final=True,
    )
    try:
        content = journal_path.read_bytes()
    except OSError as error:
        raise RunnerError("unable to read publication journal") from error
    if len(content) > 16_384:
        raise RunnerError("publication journal is too large")
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise RunnerError("invalid publication journal") from error
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
    return value


def _receipt_from_transaction(transaction: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "transaction_id": transaction["transaction_id"],
        "configuration_sha256": transaction["configuration_sha256"],
        "result_sha256": transaction["candidate_pair"]["result_sha256"],
        "report_sha256": transaction["candidate_pair"]["report_sha256"],
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
    return value


def _validate_receipt_matches(
    receipt: Mapping[str, Any],
    transaction: Mapping[str, Any],
) -> None:
    if dict(receipt) != _receipt_from_transaction(transaction):
        raise RunnerError("publication receipt does not match journal")


def _persist_journal(paths: RunnerPaths, transaction: Mapping[str, Any]) -> None:
    if os.path.lexists(paths.journal_path):
        raise RunnerError("a publication journal is already active")
    _write_new_fsynced(paths.journal_path, canonical_json_bytes(dict(transaction)))
    if _load_journal(paths) != dict(transaction):
        raise RunnerError("publication journal readback mismatch")


def _replace_journal(paths: RunnerPaths, transaction: Mapping[str, Any]) -> None:
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    update = transaction_paths["journal_update"]
    update.unlink(missing_ok=True)
    _write_new_fsynced(update, canonical_json_bytes(dict(transaction)))
    os.replace(update, paths.journal_path)
    if _load_journal(paths) != dict(transaction):
        raise RunnerError("publication journal update mismatch")


def _cleanup_transaction(
    paths: RunnerPaths,
    transaction: Mapping[str, Any],
) -> None:
    transaction_paths = _transaction_paths(paths, transaction["transaction_id"])
    for path in transaction_paths.values():
        path.unlink(missing_ok=True)
    paths.receipt_path(transaction["receipt_name"]).unlink(missing_ok=True)
    paths.journal_path.unlink(missing_ok=True)


def _discard_unjournaled(paths: RunnerPaths, transaction_id: str) -> None:
    for path in _transaction_paths(paths, transaction_id).values():
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _validate_candidate_pair(
    paths: RunnerPaths,
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_canonical_pair_metadata(paths, require_entries=True)
    try:
        result_bytes = paths.result_path.read_bytes()
        report_bytes = paths.report_path.read_bytes()
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
                previous_result = transaction_paths["previous_result"].read_bytes()
                previous_report = transaction_paths["previous_report"].read_bytes()
            except OSError as error:
                raise RunnerError("required previous-pair backup is missing") from error
            if _sha256_bytes(previous_result) != previous["result_sha256"]:
                raise RunnerError("previous result backup digest mismatch")
            if _sha256_bytes(previous_report) != previous["report_sha256"]:
                raise RunnerError("previous report backup digest mismatch")
            for key in ("restore_result", "restore_report"):
                transaction_paths[key].unlink(missing_ok=True)
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
            Path(paths.canonical_root).mkdir(parents=True, exist_ok=True)
            _validate_canonical_pair_metadata(
                paths,
                require_entries=False,
                allow_partial=True,
            )
            os.replace(transaction_paths["restore_result"], paths.result_path)
            os.replace(transaction_paths["restore_report"], paths.report_path)
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
        paths.result_path.unlink(missing_ok=True)
        paths.report_path.unlink(missing_ok=True)
    if update_state:
        state = load_state(paths)
        if state["phase"] == "awaiting_acceptance":
            _transition(paths, state, "rejected")
        elif state["phase"] != "rejected":
            raise RunnerError("recovery state does not match publication journal")
    _cleanup_transaction(paths, transaction)
    return "restored"


def _recover_locked(paths: RunnerPaths) -> str:
    if not os.path.lexists(paths.journal_path):
        return "none"
    transaction = _load_journal(paths)
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
        _assert_anchor_digests(paths, state)
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
                transaction_paths["new_result"].read_bytes() != result_bytes
                or transaction_paths["new_report"].read_bytes() != report_bytes
            ):
                raise RunnerError("staged candidate readback mismatch")
            result_exists = os.path.lexists(paths.result_path)
            report_exists = os.path.lexists(paths.report_path)
            if result_exists != report_exists:
                raise RunnerError("partial canonical pair")
            previous_result_sha256: str | None = None
            previous_report_sha256: str | None = None
            if result_exists:
                previous_result = paths.result_path.read_bytes()
                previous_report = paths.report_path.read_bytes()
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
            Path(paths.canonical_root).mkdir(parents=True, exist_ok=True)
            _validate_canonical_pair_metadata(paths, require_entries=False)
            os.replace(transaction_paths["new_result"], paths.result_path)
            os.replace(transaction_paths["new_report"], paths.report_path)
            _validate_candidate_pair(paths, transaction)
            receipt = _receipt_from_transaction(transaction)
            _write_new_fsynced(receipt_path, canonical_json_bytes(receipt))
            if _load_receipt(paths, receipt_path) != receipt:
                raise RunnerError("publication receipt readback mismatch")
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
                    _restore_transaction(paths, transaction, update_state=False)
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
            _config, _split, _ledger, digests = _validate_preflight_inputs(paths)
            for field, digest in digests.items():
                if state[field] != digest:
                    label = field.removesuffix("_sha256").replace("_", " ")
                    raise RunnerError(f"{label} changed after preflight")
            if (
                transaction["configuration_sha256"]
                != state["configuration_sha256"]
            ):
                raise RunnerError("journal configuration does not match runner state")
            _validate_candidate_pair(paths, transaction)
        except RunnerError as error:
            if transaction is not None:
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
        transaction = _load_journal(paths)
        try:
            transaction, _receipt = _load_matching_transaction_and_receipt(
                paths,
                Path(receipt_path),
                transaction=transaction,
            )
        except RunnerError:
            try:
                _restore_transaction(paths, transaction, update_state=True)
            except Exception as restore_error:
                raise RunnerError(
                    "rejection receipt failed and previous-pair restoration failed"
                ) from restore_error
            raise
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
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--input-root")
    parser.add_argument("--state-root")
    parser.add_argument("--canonical-root")
    parser.add_argument("--config")
    parser.add_argument("--environment-lock")
    parser.add_argument("--feature-schema")
    parser.add_argument("--split-manifest")
    parser.add_argument("--input-ledger")
    parser.add_argument("--non-lockbox-packet")
    parser.add_argument("--lockbox-result")
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
    defaults = RunnerPaths.from_project_root(Path(arguments.project_root))
    updates = {
        "input_root": arguments.input_root,
        "state_root": arguments.state_root,
        "canonical_root": arguments.canonical_root,
        "config_path": arguments.config,
        "environment_lock_path": arguments.environment_lock,
        "feature_schema_path": arguments.feature_schema,
        "split_manifest_path": arguments.split_manifest,
        "input_ledger_path": arguments.input_ledger,
        "non_lockbox_packet_path": arguments.non_lockbox_packet,
        "lockbox_result_path": arguments.lockbox_result,
    }
    return replace(
        defaults,
        **{
            field: Path(value)
            for field, value in updates.items()
            if value is not None
        },
    )


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
