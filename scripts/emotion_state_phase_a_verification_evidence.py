"""Deterministic, offline verification primitives for EMOTION-STATE Phase A."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARD_POLICY_RELATIVE_PATH = (
    "research/sources/emotion_state/phase_a_verification_guard_policy.json"
)
GUARD_POLICY_PATH = ROOT / GUARD_POLICY_RELATIVE_PATH
FROZEN_GUARD_POLICY_DIGEST = (
    "A750C3EB69EB35D100AB32C9DCAFA9E02D2C91BD2BF8BACD6AB7F39899FC0DDE"
)

POLICY_ID = "emotion-state-phase-a-verification-guard-v1"
SCHEMA_VERSION = 1
NETWORK_ALLOWED = False
PRIVATE_PATH_PREFIXES = ("data/private", "data/private-restricted")
PRIVATE_GITIGNORE_SENTINEL_RELATIVE_PATH = "data/private/.gitignore"
PRIVATE_GITIGNORE_SENTINEL_BYTES = b"*\n!.gitignore\n"
PARENT_ENVIRONMENT_ALLOWLIST = (
    "COMSPEC",
    "PATH",
    "PATHEXT",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "WINDIR",
)
GUARD_GENERATED_ENVIRONMENT_NAMES = (
    "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON",
    "EMOTION_STATE_PHASE_A_GUARD_POLICY",
    "EMOTION_STATE_PHASE_A_PROJECT_ROOT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_TERMINAL_PROMPT",
    "HOME",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONIOENCODING",
    "PYTHONPATH",
    "PYTHONUTF8",
    "TEMP",
    "TMP",
    "USERPROFILE",
)
PROVIDER_ENVIRONMENT_EXACT_NAMES = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "CARTESIA_API_KEY",
    "DIALOGUE_REASONER_API_KEY",
    "ELEVENLABS_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "LOCAL_DIALOGUE_REASONER_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_SECRET",
    "OPENROUTER_API_KEY",
    "TOGETHER_API_KEY",
    "TOOL_AUTH_TOKEN",
    "ULTRAVOX_API_KEY",
)
PROVIDER_ENVIRONMENT_PREFIXES = (
    "ASSEMBLYAI_",
    "AWS_",
    "CARTESIA_",
    "DEEPGRAM_",
    "DIALOGUE_REASONER_",
    "ELEVENLABS_",
    "GH_",
    "GITHUB_",
    "GROQ_",
    "HF_",
    "HUGGING_FACE_",
    "LOCAL_DIALOGUE_REASONER_",
    "OPENAI_",
    "OPENROUTER_",
    "TOGETHER_",
    "TWILIO_",
    "ULTRAVOX_",
)
CREDENTIAL_ENVIRONMENT_NAME_PATTERN = (
    r"(^|_)(API_KEY|ACCESS_KEY|ACCESS_TOKEN|AUTH_TOKEN|BEARER_TOKEN|"
    r"PRIVATE_KEY|SECRET|TOKEN|PASSWORD)$"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "_socket",
    "aiohttp",
    "assemblyai",
    "cartesia",
    "ctypes",
    "deepgram",
    "elevenlabs",
    "ftplib",
    "github",
    "groq",
    "http",
    "httpx",
    "openai",
    "openrouter",
    "requests",
    "socket",
    "together",
    "twilio",
    "ultravox",
    "urllib",
)
OUTPUT_EXCLUSIONS = (
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json",
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md",
    ".tmp/emotion-state-001-phase-a-publication/**",
)
CANONICAL_OUTPUT_FILES = ("result.json", "report.md")
PUBLICATION_RECOVERY_RELATIVE_PATH = (
    ".tmp/emotion-state-001-phase-a-publication"
)
PUBLICATION_LOCK_NAME = "publication.lock"
GUARD_IMPLEMENTATION_RELATIVE_PATH = (
    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
)
REVIEWED_EXECUTABLE_ROOTS = (
    "scripts/run_emotion_state_001_phase_a_contracts.py",
    "scripts/emotion_state_phase_a_contracts.py",
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/validate_emotion_state_001_phase_a_contracts.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_annotation_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/test_emotion_state_001_open_dataset_gate.py",
    "scripts/test_emotion_state_001_closeout_hardening.py",
    "scripts/validate_exp_002_frozen_response_baseline.py",
    "scripts/validate_brain_002_runtime_state_schema.py",
)
GATE_MODULE_PATHS = (
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/emotion_state_annotation_contracts.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/emotion_state_phase_a_verification_evidence.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
)
ALLOWED_COMMAND_TEMPLATES = (
    (
        "focused-open-dataset-tests",
        (
            "python",
            "-m",
            "unittest",
            "scripts.test_emotion_state_001_open_dataset_gate",
            "-v",
        ),
    ),
    (
        "closeout-hardening-tests",
        (
            "python",
            "-m",
            "unittest",
            "scripts.test_emotion_state_001_closeout_hardening",
            "-v",
        ),
    ),
    (
        "phase-a-prepublication-validator",
        (
            "python",
            "scripts/validate_emotion_state_001_phase_a_contracts.py",
            "--section",
            "prepublication",
            "--mode",
            "{mode}",
        ),
    ),
    (
        "phase-a-materials-validator",
        (
            "python",
            "scripts/validate_emotion_state_001_phase_a_contracts.py",
            "--section",
            "materials",
        ),
    ),
    (
        "frozen-exp-002-validator",
        ("python", "scripts/validate_exp_002_frozen_response_baseline.py"),
    ),
    (
        "brain-schema-validator",
        ("python", "scripts/validate_brain_002_runtime_state_schema.py"),
    ),
    (
        "private-boundary-validator",
        ("python", "scripts/validate_private_data_boundary.py"),
    ),
    (
        "runtime-manifest-validator",
        ("python", "scripts/validate_runtime_manifest.py"),
    ),
    ("setup-validator", ("python", "scripts/validate_check_setup.py")),
    ("drift-validator", ("python", "scripts/validate_project_drift_guard.py")),
    (
        "thesis-reference-validator",
        ("python", "scripts/check_thesis_reference_registry.py"),
    ),
    (
        "thesis-update-validator",
        ("python", "scripts/check_thesis_update_gate.py"),
    ),
    (
        "context-policy-validator",
        ("python", "scripts/validate_context_reading_policy.py"),
    ),
    (
        "json-validator",
        (
            "python",
            "scripts/emotion_state_phase_a_verification_evidence.py",
            "--validate-json-inputs",
        ),
    ),
    (
        "git-diff-check",
        (
            "git",
            "diff",
            "--check",
            "{baseline_commit}..{head_commit}",
        ),
    ),
)

REPOSITORY_GATE_COMMAND_IDS = {
    "focused_tests": ("focused-open-dataset-tests",),
    "closeout_hardening": ("closeout-hardening-tests",),
    "phase_a_prepublication": ("phase-a-prepublication-validator",),
    "materials": ("phase-a-materials-validator",),
    "frozen_exp_002": ("frozen-exp-002-validator",),
    "brain_schema": ("brain-schema-validator",),
    "private_boundary": ("private-boundary-validator",),
    "runtime_manifest": ("runtime-manifest-validator",),
    "setup": ("setup-validator",),
    "drift": ("drift-validator",),
    "thesis_reference_registry": ("thesis-reference-validator",),
    "thesis_update": ("thesis-update-validator",),
    "context_policy": ("context-policy-validator",),
    "json": ("json-validator",),
    "diff_check": ("git-diff-check",),
}

EXPECTED_GUARD_POLICY = {
    "policy_id": POLICY_ID,
    "schema_version": SCHEMA_VERSION,
    "network_allowed": NETWORK_ALLOWED,
    "private_path_prefixes": list(PRIVATE_PATH_PREFIXES),
    "parent_environment_allowlist": list(PARENT_ENVIRONMENT_ALLOWLIST),
    "guard_generated_environment_names": list(GUARD_GENERATED_ENVIRONMENT_NAMES),
    "provider_environment_exact_names": list(PROVIDER_ENVIRONMENT_EXACT_NAMES),
    "provider_environment_prefixes": list(PROVIDER_ENVIRONMENT_PREFIXES),
    "credential_environment_name_pattern": CREDENTIAL_ENVIRONMENT_NAME_PATTERN,
    "forbidden_import_prefixes": list(FORBIDDEN_IMPORT_PREFIXES),
    "output_exclusions": list(OUTPUT_EXCLUSIONS),
    "canonical_output_files": list(CANONICAL_OUTPUT_FILES),
    "allowed_commands": [
        {
            "command_id": command_id,
            "argv_template": list(argv_template),
        }
        for command_id, argv_template in ALLOWED_COMMAND_TEMPLATES
    ],
}

_CREDENTIAL_ENVIRONMENT_NAME_RE = re.compile(
    CREDENTIAL_ENVIRONMENT_NAME_PATTERN,
    re.IGNORECASE,
)
_LOWERCASE_COMMIT_RANGE_RE = re.compile(
    r"(?P<baseline>[0-9a-f]{40})\.\.(?P<head>[0-9a-f]{40})"
)
_CANONICAL_COMMAND_KEYS = (
    "sequence_number",
    "command_id",
    "argv",
    "working_directory",
    "exit_status",
)
_VALID_MODES = ("material-pending", "complete")
_DERIVED_COMPLETION_FIELDS = {
    "repository_gate_statuses",
    "guarded_command_results",
}
_GIT_TIMEOUT_SECONDS = 30
_GUARDED_COMMAND_TIMEOUT_SECONDS = 180
_INLINE_SOURCE_DIGESTS = {
    "private_path_probe": (
        "67BE07A2010F3F5F7857E274F59A523196A8B2071270043F5A30D0C80E849662"
    ),
    "network_probe": (
        "D0E83A77224E603F97B3DE9B25983BB4AA27C3116BE66FE11B922813AAADE8AA"
    ),
    "credential_probe": (
        "B2D78EC951F391DD6167342124D80968AD88C9D72C7F7F1B082D273AFA531886"
    ),
    "process_bypass_probe": (
        "0C84AD0AB699783710EE7729306E5D8763C8013297A26BE3197EA68AE3500A67"
    ),
    "closeout_lock_holder": (
        "6A2DA06455D5DAD127FF5C6446BE3CCB247A7258BFD2E5ECC12D363E70C72473"
    ),
}


def canonical_json_bytes(value: object) -> bytes:
    """Return the canonical UTF-8 JSON representation used by evidence digests."""

    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    """Return an uppercase SHA-256 digest for exact bytes."""

    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    return hashlib.sha256(content).hexdigest().upper()


def sha256_file(path: Path) -> str:
    """Return an uppercase SHA-256 digest for the exact file bytes."""

    return sha256_bytes(Path(path).read_bytes())


def canonical_json_sha256(value: object) -> str:
    """Return the uppercase SHA-256 digest of canonical JSON bytes."""

    return sha256_bytes(canonical_json_bytes(value))


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _load_json_bytes(content: bytes, *, source: str) -> Any:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{source} is not UTF-8 JSON") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(
            ("duplicate JSON key:", "invalid JSON constant:")
        ):
            raise
        raise ValueError(f"{source} is not valid JSON: {exc}") from exc


def _assert_exact_policy_value(
    actual: object,
    expected: object,
    *,
    location: str,
) -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"guard policy differs at {location}")
    if isinstance(expected, dict):
        actual_mapping = actual
        if tuple(actual_mapping) != tuple(expected):
            raise ValueError(f"guard policy key order differs at {location}")
        for key, expected_value in expected.items():
            _assert_exact_policy_value(
                actual_mapping[key],
                expected_value,
                location=f"{location}.{key}",
            )
        return
    if isinstance(expected, list):
        actual_list = actual
        if len(actual_list) != len(expected):
            raise ValueError(f"guard policy list length differs at {location}")
        for index, (actual_value, expected_value) in enumerate(
            zip(actual_list, expected, strict=True)
        ):
            _assert_exact_policy_value(
                actual_value,
                expected_value,
                location=f"{location}[{index}]",
            )
        return
    if actual != expected:
        raise ValueError(f"guard policy differs at {location}")


def load_guard_policy(path: Path = GUARD_POLICY_PATH) -> dict[str, Any]:
    """Load the exact reviewed guard-policy bytes."""

    policy_path = Path(path)
    try:
        policy_bytes = policy_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"guard policy could not be read: {policy_path}") from exc
    if sha256_bytes(policy_bytes) != FROZEN_GUARD_POLICY_DIGEST:
        raise ValueError("guard policy bytes differ from the frozen policy")
    policy = _load_json_bytes(policy_bytes, source="guard policy")
    _assert_exact_policy_value(policy, EXPECTED_GUARD_POLICY, location="$")

    command_ids = [
        command["command_id"] for command in policy["allowed_commands"]
    ]
    command_templates = [
        tuple(command["argv_template"]) for command in policy["allowed_commands"]
    ]
    if len(command_ids) != len(set(command_ids)):
        raise ValueError("guard policy command IDs must be unique")
    if len(command_templates) != len(set(command_templates)):
        raise ValueError("guard policy command templates must be unique")
    substitutions = {
        substitution
        for command in policy["allowed_commands"]
        for argument in command["argv_template"]
        for substitution in re.findall(r"\{([a-z_]+)\}", argument)
    }
    if substitutions != {"baseline_commit", "head_commit", "mode"}:
        raise ValueError("guard policy substitutions are not closed")
    return policy


GUARD_POLICY_BYTES = GUARD_POLICY_PATH.read_bytes()
GUARD_POLICY = load_guard_policy()
GUARD_POLICY_DIGEST = sha256_bytes(GUARD_POLICY_BYTES)


def _normalize_relative_path(value: str, *, label: str, allow_dot: bool) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{label} must be a non-empty relative path")
    if PureWindowsPath(value).drive or PureWindowsPath(value).root:
        raise ValueError(f"{label} must be relative")
    normalized_input = value.replace("\\", "/")
    pure_path = PurePosixPath(normalized_input)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(f"{label} escapes the repository root")
    normalized = pure_path.as_posix()
    if normalized == "." and not allow_dot:
        raise ValueError(f"{label} must name a file")
    return normalized


def _is_absolute_path_argument(argument: str) -> bool:
    windows_path = PureWindowsPath(argument)
    return (
        bool(windows_path.drive)
        or bool(windows_path.root)
        or PurePosixPath(argument.replace("\\", "/")).is_absolute()
    )


def canonical_command_entry(
    *,
    sequence_number: int,
    command_id: str,
    argv: Sequence[str],
    working_directory: str,
    exit_status: int,
) -> dict[str, object]:
    """Build a normalized, timestamp-free command-ledger entry."""

    if type(sequence_number) is not int or sequence_number < 1:
        raise ValueError("sequence_number must be a positive integer")
    if not isinstance(command_id, str) or not command_id or "\x00" in command_id:
        raise ValueError("command_id must be a non-empty string")
    if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence):
        raise ValueError("argv must be a sequence of strings")
    normalized_argv: list[str] = []
    for argument in argv:
        if not isinstance(argument, str) or "\x00" in argument:
            raise ValueError("argv must contain only strings")
        if _is_absolute_path_argument(argument):
            raise ValueError("canonical ledger argv must not contain absolute paths")
        normalized_argv.append(argument)
    if not normalized_argv:
        raise ValueError("argv must not be empty")
    normalized_working_directory = _normalize_relative_path(
        working_directory,
        label="working_directory",
        allow_dot=True,
    )
    if type(exit_status) is not int:
        raise ValueError("exit_status must be an integer")
    return {
        "sequence_number": sequence_number,
        "command_id": command_id,
        "argv": normalized_argv,
        "working_directory": normalized_working_directory,
        "exit_status": exit_status,
    }


def _is_credential_environment_name(name: str) -> bool:
    uppercase_name = name.upper()
    return (
        uppercase_name in PROVIDER_ENVIRONMENT_EXACT_NAMES
        or any(
            uppercase_name.startswith(prefix)
            for prefix in PROVIDER_ENVIRONMENT_PREFIXES
        )
        or _CREDENTIAL_ENVIRONMENT_NAME_RE.search(uppercase_name) is not None
    )


def _validated_environment_items(
    environment: Mapping[str, str],
    *,
    label: str,
) -> list[tuple[str, str, str]]:
    if not isinstance(environment, Mapping):
        raise ValueError(f"{label} must be a mapping")
    normalized_items: list[tuple[str, str, str]] = []
    seen_names: set[str] = set()
    for name, value in environment.items():
        if not isinstance(name, str) or not name or "\x00" in name:
            raise ValueError(f"{label} contains an invalid environment name")
        uppercase_name = name.upper()
        if uppercase_name in seen_names:
            raise ValueError(
                f"{label} contains a case-insensitive duplicate: {name}"
            )
        if not isinstance(value, str):
            raise ValueError(f"{label} value must be text for: {name}")
        seen_names.add(uppercase_name)
        normalized_items.append((name, uppercase_name, value))
    return normalized_items


def build_guarded_child_environment(
    parent_environment: Mapping[str, str],
    injected_environment: Mapping[str, str],
) -> tuple[dict[str, str], list[str]]:
    """Build a child environment from the exact reviewed allowlists."""

    cleaned: dict[str, str] = {}
    removed_names: list[str] = []
    parent_allowlist = set(PARENT_ENVIRONMENT_ALLOWLIST)
    for original_name, uppercase_name, value in _validated_environment_items(
        parent_environment,
        label="parent_environment",
    ):
        if (
            uppercase_name not in parent_allowlist
            or _is_credential_environment_name(uppercase_name)
        ):
            removed_names.append(original_name)
            continue
        cleaned[uppercase_name] = value

    injectable_names = set(GUARD_GENERATED_ENVIRONMENT_NAMES)
    for original_name, uppercase_name, value in _validated_environment_items(
        injected_environment,
        label="injected_environment",
    ):
        if _is_credential_environment_name(uppercase_name):
            raise ValueError(
                "credential-looking injected environment name is blocked: "
                f"{original_name}"
            )
        if uppercase_name not in injectable_names:
            raise ValueError(
                f"injected environment name is not policy-listed: {original_name}"
            )
        cleaned[uppercase_name] = value

    removed_names.sort(key=lambda name: (name.upper(), name))
    return cleaned, removed_names


def _python_inline_rule(
    *,
    caller: str,
    source_sha256: str,
    cwd_class: str,
    environment_class: str,
    max_uses: int,
) -> dict[str, object]:
    return {
        "kind": "python_inline",
        "caller": caller,
        "source_sha256": source_sha256,
        "cwd_class": cwd_class,
        "environment_class": environment_class,
        "max_uses": max_uses,
        "children": [],
    }


def _python_target_rule(
    *,
    caller: str,
    target: str,
    args: Sequence[str] = (),
    cwd_class: str = "project_root",
    environment_class: str = "inherit",
    max_uses: int = 1,
) -> dict[str, object]:
    return {
        "kind": "python_target",
        "caller": caller,
        "target": target,
        "args": list(args),
        "cwd_class": cwd_class,
        "environment_class": environment_class,
        "max_uses": max_uses,
        "children": [],
    }


def _git_rule(
    *,
    caller: str,
    matcher_id: str,
    cwd_class: str,
    captured_head: str | None = None,
    sentinel_object_id: str | None = None,
) -> dict[str, object]:
    rule: dict[str, object] = {
        "kind": "git",
        "caller": caller,
        "matcher_id": matcher_id,
        "cwd_class": cwd_class,
        "children": [],
    }
    if captured_head is not None or sentinel_object_id is not None:
        if captured_head is None or sentinel_object_id is None:
            raise ValueError("sentinel Git rule values must be supplied together")
        rule["captured_head"] = captured_head
        rule["sentinel_object_id"] = sentinel_object_id
    return rule


def _capture_project_root_sentinel_values(root: Path) -> tuple[str, str]:
    head_lines = _run_git_bytes(
        root,
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    ).decode("ascii", errors="strict").splitlines()
    if (
        len(head_lines) != 1
        or re.fullmatch(r"[0-9a-f]{40}", head_lines[0]) is None
    ):
        raise ValueError("private sentinel HEAD is unavailable")
    captured_head = head_lines[0]
    tree_record = _run_git_bytes(
        root,
        "ls-tree",
        "-z",
        captured_head,
        "--",
        f":(literal){PRIVATE_GITIGNORE_SENTINEL_RELATIVE_PATH}",
    )
    mode, sentinel_object_id = _parse_git_object_record(
        tree_record,
        expected_path=PRIVATE_GITIGNORE_SENTINEL_RELATIVE_PATH,
        source="private sentinel Git tree entry",
    )
    if mode not in {"100644", "100755"}:
        raise ValueError("private sentinel Git tree entry is not a regular blob")
    return captured_head, sentinel_object_id


def _command_subprocess_rules(
    *,
    command_id: str,
    root: Path,
) -> list[dict[str, object]]:
    verification_caller = (
        "scripts/emotion_state_phase_a_verification_evidence.py"
    )
    open_dataset_test_caller = (
        "scripts/test_emotion_state_001_open_dataset_gate.py"
    )
    if command_id == "focused-open-dataset-tests":
        return [
            _python_inline_rule(
                caller=open_dataset_test_caller,
                source_sha256=_INLINE_SOURCE_DIGESTS["private_path_probe"],
                cwd_class="transaction_descendant",
                environment_class="synthetic_guard",
                max_uses=1,
            ),
            _python_inline_rule(
                caller=open_dataset_test_caller,
                source_sha256=_INLINE_SOURCE_DIGESTS["network_probe"],
                cwd_class="transaction_descendant",
                environment_class="synthetic_guard",
                max_uses=1,
            ),
            _python_inline_rule(
                caller=open_dataset_test_caller,
                source_sha256=_INLINE_SOURCE_DIGESTS["credential_probe"],
                cwd_class="transaction_descendant",
                environment_class="synthetic_guard",
                max_uses=1,
            ),
            _python_inline_rule(
                caller=open_dataset_test_caller,
                source_sha256=_INLINE_SOURCE_DIGESTS[
                    "process_bypass_probe"
                ],
                cwd_class="transaction_descendant",
                environment_class="synthetic_guard",
                max_uses=1,
            ),
            _python_target_rule(
                caller=verification_caller,
                target="scripts/validate_context_reading_policy.py",
                environment_class="guarded_child",
            ),
            _git_rule(
                caller=open_dataset_test_caller,
                matcher_id="transaction_fixture",
                cwd_class="transaction_descendant",
            ),
            _git_rule(
                caller=verification_caller,
                matcher_id="transaction_verification",
                cwd_class="transaction_descendant",
            ),
        ]
    if command_id == "closeout-hardening-tests":
        closeout_caller = (
            "scripts/test_emotion_state_001_closeout_hardening.py"
        )
        return [
            _python_inline_rule(
                caller=closeout_caller,
                source_sha256=_INLINE_SOURCE_DIGESTS[
                    "closeout_lock_holder"
                ],
                cwd_class="project_root",
                environment_class="inherit",
                max_uses=1,
            ),
            _python_target_rule(
                caller=closeout_caller,
                target="scripts/run_emotion_state_001_phase_a_contracts.py",
                max_uses=2,
            ),
        ]
    if command_id == "frozen-exp-002-validator":
        caller = "scripts/validate_exp_002_frozen_response_baseline.py"
        return [
            _python_target_rule(
                caller=caller,
                target="scripts/run_exp_002_frozen_response_baseline.py",
            ),
            _python_target_rule(
                caller=caller,
                target="scripts/run_prompt_baseline.py",
                args=(
                    "--cases",
                    str(
                        root
                        / "research/experiments/cases/"
                        "exp-002-dataset-derived.json"
                    ),
                    "--out",
                    str(
                        root
                        / ".tmp/exp-002-frozen-response-baseline/"
                        "EXP-002-prompt-packet.md"
                    ),
                ),
            ),
        ]
    if command_id == "brain-schema-validator":
        caller = "scripts/validate_brain_002_runtime_state_schema.py"
        return [
            _python_target_rule(
                caller=caller,
                target="scripts/run_brain_002_runtime_state_schema.py",
                args=(
                    "--out",
                    str(
                        root
                        / "research/experiments/generated/"
                        "BRAIN-002-runtime-state-schema/result.json"
                    ),
                    "--report-out",
                    str(
                        root
                        / "research/experiments/generated/"
                        "BRAIN-002-runtime-state-schema/report.md"
                    ),
                ),
            )
        ]
    if command_id in {
        "private-boundary-validator",
        "setup-validator",
        "drift-validator",
    }:
        captured_head, sentinel_object_id = (
            _capture_project_root_sentinel_values(root)
        )
        return [
            _git_rule(
                caller=verification_caller,
                matcher_id="project_root_sentinel",
                cwd_class="project_root",
                captured_head=captured_head,
                sentinel_object_id=sentinel_object_id,
            )
        ]
    if command_id == "thesis-update-validator":
        return [
            _git_rule(
                caller="scripts/check_thesis_update_gate.py",
                matcher_id="thesis_status",
                cwd_class="project_root",
            )
        ]
    return []


def _required_command_substitutions(
    argv_template: Sequence[str],
) -> set[str]:
    return {
        substitution
        for argument in argv_template
        for substitution in re.findall(r"\{([a-z_]+)\}", argument)
    }


def _render_guarded_command(
    *,
    command_id: str,
    argv_template: tuple[str, ...],
    substitutions: Mapping[str, str],
) -> list[str]:
    required_substitutions = _required_command_substitutions(argv_template)
    if set(substitutions) != required_substitutions:
        raise ValueError(
            f"{command_id} requires substitutions: "
            + ", ".join(sorted(required_substitutions))
        )
    normalized_substitutions: dict[str, str] = {}
    for name in sorted(required_substitutions):
        value = substitutions[name]
        if not isinstance(value, str):
            raise ValueError(f"{name} substitution must be text")
        if name == "mode":
            if value not in _VALID_MODES:
                raise ValueError("mode substitution is not reviewed")
        elif re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise ValueError(f"{name} must be a lowercase 40-hex commit")
        normalized_substitutions[name] = value
    canonical_argv = [
        argument.format(**normalized_substitutions)
        for argument in argv_template
    ]
    if len(canonical_argv) != len(argv_template):
        raise ValueError("rendered guarded command length mismatch")
    for rendered, template in zip(
        canonical_argv,
        argv_template,
        strict=True,
    ):
        if template.startswith("{") or "{" in template:
            expected = template.format(**normalized_substitutions)
            if rendered != expected:
                raise ValueError("rendered guarded command substitution drift")
        elif rendered != template:
            raise ValueError("rendered guarded command template drift")
    return canonical_argv


def _same_filesystem_path(first: Path, second: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(first))) == os.path.normcase(
        os.path.normpath(str(second))
    )


def _strict_lexical_descendant(candidate: Path, root: Path) -> bool:
    try:
        common = os.path.commonpath((str(candidate), str(root)))
    except ValueError:
        return False
    return (
        os.path.normcase(os.path.normpath(common))
        == os.path.normcase(os.path.normpath(str(root)))
        and not _same_filesystem_path(candidate, root)
    )


def _path_is_link_or_reparse(path: Path) -> bool:
    status = path.lstat()
    reparse_attribute = getattr(
        stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        0x400,
    )
    return stat.S_ISLNK(status.st_mode) or bool(
        getattr(status, "st_file_attributes", 0) & reparse_attribute
    )


def _validate_exact_non_link_path(
    path: Path,
    *,
    root: Path,
    label: str,
    require_directory: bool,
) -> Path:
    root_path = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(path))
    if not _strict_lexical_descendant(candidate, root_path):
        raise ValueError(f"{label} is not an exact root descendant")
    try:
        relative_parts = candidate.relative_to(root_path).parts
    except ValueError as exc:
        raise ValueError(f"{label} escapes the guarded root") from exc
    current = root_path
    for part in relative_parts:
        current = current / part
        if not os.path.lexists(current):
            raise ValueError(f"{label} is unavailable")
        try:
            if _path_is_link_or_reparse(current):
                raise ValueError(f"{label} traverses a link or reparse point")
            resolved = current.resolve(strict=True)
        except OSError as exc:
            raise ValueError(f"{label} could not be resolved") from exc
        if not _same_filesystem_path(resolved, current):
            raise ValueError(f"{label} does not resolve exactly")
        if not (
            _same_filesystem_path(resolved, root_path)
            or _strict_lexical_descendant(resolved, root_path)
        ):
            raise ValueError(f"{label} resolves outside the guarded root")
    if require_directory:
        if not candidate.is_dir():
            raise ValueError(f"{label} is not a directory")
    elif not candidate.is_file():
        raise ValueError(f"{label} is not a file")
    return candidate


def _ensure_exact_non_link_directory(
    path: Path,
    *,
    root: Path,
    label: str,
) -> Path:
    root_path = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(path))
    if not _strict_lexical_descendant(candidate, root_path):
        raise ValueError(f"{label} is not an exact root descendant")
    try:
        relative_parts = candidate.relative_to(root_path).parts
    except ValueError as exc:
        raise ValueError(f"{label} escapes the guarded root") from exc
    current = root_path
    for part in relative_parts:
        current = current / part
        if not os.path.lexists(current):
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                pass
            except OSError as exc:
                raise ValueError(f"{label} could not be created") from exc
        _validate_exact_non_link_path(
            current,
            root=root_path,
            label=label,
            require_directory=True,
        )
    return candidate


@contextmanager
def _fresh_guarded_transaction_directory(
    recovery_root: Path,
    project_root: Path | None = None,
) -> Iterator[Path]:
    recovery_path = Path(os.path.abspath(recovery_root))
    if project_root is None:
        if (
            recovery_path.name
            != PurePosixPath(PUBLICATION_RECOVERY_RELATIVE_PATH).name
            or recovery_path.parent.name != ".tmp"
        ):
            raise ValueError("guarded command recovery root is not exact")
        project_path = recovery_path.parent.parent
    else:
        project_path = Path(os.path.abspath(project_root))
    recovery_path = _ensure_exact_non_link_directory(
        recovery_path,
        root=project_path,
        label="guarded command recovery root",
    )
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    for index in range(len(alphabet) ** 2):
        if index < len(alphabet):
            name = alphabet[index]
        else:
            quotient, remainder = divmod(index, len(alphabet))
            name = alphabet[quotient - 1] + alphabet[remainder]
        transaction_path = recovery_path / name
        try:
            transaction_path.mkdir(mode=0o700)
        except FileExistsError:
            continue
        except OSError as exc:
            raise ValueError(
                "unable to create guarded command transaction"
            ) from exc
        transaction_path = _validate_exact_non_link_path(
            transaction_path,
            root=project_path,
            label="guarded command transaction",
            require_directory=True,
        )
        created_status = transaction_path.lstat()
        created_identity = (created_status.st_dev, created_status.st_ino)
        try:
            yield transaction_path
        finally:
            _validate_exact_non_link_path(
                recovery_path,
                root=project_path,
                label="guarded command recovery root",
                require_directory=True,
            )
            if os.path.lexists(transaction_path):
                _validate_exact_non_link_path(
                    transaction_path,
                    root=project_path,
                    label="guarded command transaction",
                    require_directory=True,
                )
                current_status = transaction_path.lstat()
                if (
                    current_status.st_dev,
                    current_status.st_ino,
                ) != created_identity:
                    raise ValueError(
                        "guarded command transaction identity changed"
                    )
                try:
                    shutil.rmtree(transaction_path)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    raise ValueError(
                        "unable to clean guarded command transaction"
                    ) from exc
        return
    raise ValueError("no fresh guarded command transaction slot is available")


def run_guarded_command(
    command_id: str,
    root: Path,
    substitutions: Mapping[str, str],
) -> dict[str, object]:
    """Execute one exact policy command under a fresh fail-closed guard."""

    try:
        root_path = Path(root).resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise ValueError("guarded command root is unavailable") from exc
    if not root_path.is_dir():
        raise ValueError("guarded command root must be a directory")
    policy_path = root_path.joinpath(
        *PurePosixPath(GUARD_POLICY_RELATIVE_PATH).parts
    )
    policy_path = _validate_exact_non_link_path(
        policy_path,
        root=root_path,
        label="guard policy path",
        require_directory=False,
    )
    policy = load_guard_policy(policy_path)
    commands_by_id = {
        command["command_id"]: tuple(command["argv_template"])
        for command in policy["allowed_commands"]
    }
    if command_id not in commands_by_id:
        raise ValueError(f"unknown guarded command ID: {command_id}")
    if not isinstance(substitutions, Mapping):
        raise ValueError("guarded command substitutions must be a mapping")
    canonical_argv = _render_guarded_command(
        command_id=command_id,
        argv_template=commands_by_id[command_id],
        substitutions=substitutions,
    )
    guard_site_path = root_path / "scripts/emotion_state_phase_a_guard_site"
    guard_site_file = guard_site_path / "sitecustomize.py"
    _validate_exact_non_link_path(
        guard_site_file,
        root=root_path,
        label="guard site path",
        require_directory=False,
    )
    rules = _command_subprocess_rules(
        command_id=command_id,
        root=root_path,
    )
    recovery_root = root_path.joinpath(
        *PurePosixPath(PUBLICATION_RECOVERY_RELATIVE_PATH).parts
    )
    with _fresh_guarded_transaction_directory(
        recovery_root,
        root_path,
    ) as transaction_path:
        injected_environment = {
            "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON": (
                json.dumps(
                    rules,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                    allow_nan=False,
                )
            ),
            "EMOTION_STATE_PHASE_A_GUARD_POLICY": str(policy_path),
            "EMOTION_STATE_PHASE_A_PROJECT_ROOT": str(root_path),
            "GIT_CONFIG_GLOBAL": "NUL",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": str(transaction_path),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": os.pathsep.join((
                str(guard_site_path),
                str(root_path),
            )),
            "PYTHONUTF8": "1",
            "TEMP": str(transaction_path),
            "TMP": str(transaction_path),
            "USERPROFILE": str(transaction_path),
        }
        child_environment, _removed_names = build_guarded_child_environment(
            parent_environment=os.environ,
            injected_environment=injected_environment,
        )
        if canonical_argv[0] == "python":
            execution_argv = [sys.executable, *canonical_argv[1:]]
        else:
            execution_argv = ["git", "--no-lazy-fetch", *canonical_argv[1:]]
        try:
            completed = subprocess.run(
                execution_argv,
                cwd=root_path,
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                shell=False,
                timeout=_GUARDED_COMMAND_TIMEOUT_SECONDS,
                close_fds=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(
                f"guarded command timed out: {command_id}"
            ) from exc
        except OSError as exc:
            raise ValueError(
                f"guarded command could not start: {command_id}"
            ) from exc
        return canonical_command_entry(
            sequence_number=1,
            command_id=command_id,
            argv=canonical_argv,
            working_directory=".",
            exit_status=completed.returncode,
        )


def _expected_mode_commands(
    mode: str,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if mode not in _VALID_MODES:
        raise ValueError(f"unsupported verification mode: {mode}")
    if mode == "material-pending":
        return tuple(
            command
            for command in ALLOWED_COMMAND_TEMPLATES
            if command[0] != "phase-a-materials-validator"
        )
    return ALLOWED_COMMAND_TEMPLATES


def _validate_argv_template(
    actual_argv: list[str],
    argv_template: tuple[str, ...],
    *,
    mode: str,
) -> None:
    if len(actual_argv) != len(argv_template):
        raise ValueError("command argv does not match the guard policy template")
    for actual, template in zip(actual_argv, argv_template, strict=True):
        if template == "{mode}":
            if actual != mode:
                raise ValueError("command argv mode substitution mismatch")
            continue
        if template == "{baseline_commit}..{head_commit}":
            if _LOWERCASE_COMMIT_RANGE_RE.fullmatch(actual) is None:
                raise ValueError("command argv commit substitution mismatch")
            continue
        if actual != template:
            raise ValueError("command argv does not match the guard policy template")


def derive_repository_gate_statuses(
    ledger: Sequence[Mapping[str, object]],
    mode: str,
) -> dict[str, str]:
    """Validate the exact mode ledger and derive repository-gate pass statuses."""

    if isinstance(ledger, (str, bytes)) or not isinstance(ledger, Sequence):
        raise ValueError("executed command ledger must be a sequence")
    expected_commands = _expected_mode_commands(mode)
    if len(ledger) != len(expected_commands):
        raise ValueError("executed command ledger has the wrong command count")

    present_command_ids: set[str] = set()
    for sequence_number, (entry, expected_command) in enumerate(
        zip(ledger, expected_commands, strict=True),
        start=1,
    ):
        if not isinstance(entry, Mapping):
            raise ValueError("executed command ledger entry must be a mapping")
        if set(entry) != set(_CANONICAL_COMMAND_KEYS):
            raise ValueError("executed command ledger entry has non-canonical fields")
        canonical_entry = canonical_command_entry(
            sequence_number=entry["sequence_number"],
            command_id=entry["command_id"],
            argv=entry["argv"],
            working_directory=entry["working_directory"],
            exit_status=entry["exit_status"],
        )
        expected_command_id, expected_argv_template = expected_command
        if canonical_entry["sequence_number"] != sequence_number:
            raise ValueError("executed command ledger sequence is not contiguous")
        if canonical_entry["command_id"] != expected_command_id:
            raise ValueError("executed command ledger command order mismatch")
        if canonical_entry["working_directory"] != ".":
            raise ValueError("executed command ledger working directory must be '.'")
        if canonical_entry["exit_status"] != 0:
            raise ValueError("executed command ledger contains a nonzero exit status")
        actual_argv = canonical_entry["argv"]
        _validate_argv_template(
            actual_argv,
            expected_argv_template,
            mode=mode,
        )
        present_command_ids.add(expected_command_id)

    statuses: dict[str, str] = {}
    for gate_id, command_ids in REPOSITORY_GATE_COMMAND_IDS.items():
        if all(command_id in present_command_ids for command_id in command_ids):
            statuses[gate_id] = "pass"
    return statuses


def validate_completion_evidence_request(
    request: Mapping[str, object],
) -> dict[str, object]:
    """Validate caller-owned completion evidence without accepting projections."""

    if not isinstance(request, Mapping):
        raise ValueError("completion evidence request must be a mapping")
    supplied_derived_fields = _DERIVED_COMPLETION_FIELDS.intersection(request)
    if supplied_derived_fields:
        names = ", ".join(sorted(supplied_derived_fields))
        raise ValueError(
            f"completion evidence fields are derived-only and cannot be supplied: {names}"
        )
    expected_fields = {"mode", "executed_command_ledger"}
    if set(request) != expected_fields:
        raise ValueError(
            "completion evidence request must contain only mode and "
            "executed_command_ledger"
        )
    mode = request["mode"]
    if not isinstance(mode, str):
        raise ValueError("completion evidence mode must be text")
    ledger = request["executed_command_ledger"]
    derive_repository_gate_statuses(ledger, mode)
    return {
        "mode": mode,
        "executed_command_ledger": [
            dict(entry)
            for entry in ledger
        ],
    }


def _is_private_relative_path(relative_path: str) -> bool:
    comparable_path = relative_path.casefold()
    return any(
        comparable_path == prefix.casefold()
        or comparable_path.startswith(prefix.casefold() + "/")
        for prefix in PRIVATE_PATH_PREFIXES
    )


def validate_json_inputs(
    *,
    root: Path,
    changed_json_paths: Sequence[str],
    closure_json_paths: Sequence[str],
) -> tuple[str, ...]:
    """Parse all derived JSON inputs with containment and duplicate-key checks."""

    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("JSON validation root must be a directory")
    if isinstance(changed_json_paths, (str, bytes)) or not isinstance(
        changed_json_paths,
        Sequence,
    ):
        raise ValueError("changed_json_paths must be a sequence")
    if isinstance(closure_json_paths, (str, bytes)) or not isinstance(
        closure_json_paths,
        Sequence,
    ):
        raise ValueError("closure_json_paths must be a sequence")

    normalized_paths: dict[str, str] = {}
    for source_paths in (changed_json_paths, closure_json_paths):
        for supplied_path in source_paths:
            normalized_path = _normalize_relative_path(
                supplied_path,
                label="JSON input path",
                allow_dot=False,
            )
            if _is_private_relative_path(normalized_path):
                raise ValueError("JSON input path targets a private data boundary")
            if PurePosixPath(normalized_path).suffix.casefold() != ".json":
                raise ValueError("derived JSON input path must end in .json")
            normalized_paths.setdefault(
                normalized_path.casefold(),
                normalized_path,
            )

    ordered_paths = tuple(
        sorted(
            normalized_paths.values(),
            key=lambda value: (value.casefold(), value),
        )
    )
    for normalized_path in ordered_paths:
        candidate = root_path.joinpath(*PurePosixPath(normalized_path).parts)
        try:
            resolved_path = candidate.resolve(strict=True)
            resolved_path.relative_to(root_path)
        except (FileNotFoundError, OSError) as exc:
            raise ValueError(
                f"derived JSON input does not exist: {normalized_path}"
            ) from exc
        except ValueError as exc:
            raise ValueError(
                f"derived JSON input path escapes the root: {normalized_path}"
            ) from exc
        if not resolved_path.is_file():
            raise ValueError(f"derived JSON input is not a file: {normalized_path}")
        _load_json_bytes(
            resolved_path.read_bytes(),
            source=f"JSON input {normalized_path}",
        )
    return ordered_paths


def _run_git_bytes(root: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "--no-lazy-fetch", *arguments],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=_GIT_TIMEOUT_SECONDS,
            close_fds=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"git command timed out: git {' '.join(arguments)}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"git command could not start: git {' '.join(arguments)}"
        ) from exc
    if completed.returncode != 0:
        error_text = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(
            f"git command failed ({completed.returncode}): "
            f"git {' '.join(arguments)}: {error_text}"
        )
    return completed.stdout


def _validate_git_commit(root: Path, commit: str, *, label: str) -> str:
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError(f"{label} must be a lowercase 40-hex commit")
    resolved = _run_git_bytes(
        root,
        "rev-parse",
        "--verify",
        f"{commit}^{{commit}}",
    ).decode("ascii", errors="strict").strip()
    if resolved != commit:
        raise ValueError(f"{label} does not resolve to the exact supplied commit")
    return commit


def _canonical_git_path(raw_path: bytes) -> str:
    try:
        decoded_path = os.fsdecode(raw_path)
    except UnicodeError as exc:
        raise ValueError("Git returned a path that cannot be decoded") from exc
    return _normalize_relative_path(
        decoded_path,
        label="Git path",
        allow_dot=False,
    )


def _parse_git_name_status_z(content: bytes) -> list[tuple[str, tuple[str, ...]]]:
    fields = content.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    changes: list[tuple[str, tuple[str, ...]]] = []
    index = 0
    while index < len(fields):
        try:
            status = fields[index].decode("ascii", errors="strict")
        except UnicodeError as exc:
            raise ValueError("Git returned a non-ASCII change status") from exc
        index += 1
        if not status or status[0] not in "ACDMRTUXB":
            raise ValueError(f"Git returned an unsupported change status: {status}")
        path_count = 2 if status[0] in {"R", "C"} else 1
        if index + path_count > len(fields):
            raise ValueError("Git returned a truncated name-status record")
        paths = tuple(
            _canonical_git_path(raw_path)
            for raw_path in fields[index : index + path_count]
        )
        index += path_count
        changes.append((status, paths))
    return changes


def _is_output_excluded(relative_path: str) -> bool:
    if relative_path in OUTPUT_EXCLUSIONS[:2]:
        return True
    transaction_prefix = OUTPUT_EXCLUSIONS[2][:-2]
    return relative_path.startswith(transaction_prefix)


def _parse_git_object_record(
    content: bytes,
    *,
    expected_path: str,
    source: str,
) -> tuple[str, str]:
    records = content.split(b"\0")
    records = [record for record in records if record]
    if len(records) != 1:
        raise ValueError(f"{source} does not contain exactly one Git object")
    try:
        metadata, raw_path = records[0].split(b"\t", 1)
        mode, object_type, object_id = metadata.decode(
            "ascii",
            errors="strict",
        ).split(" ", 2)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f"{source} has an invalid Git object record") from exc
    if _canonical_git_path(raw_path) != expected_path:
        raise ValueError(f"{source} returned a different path")
    if object_type != "blob" or re.fullmatch(r"[0-9a-f]{40,64}", object_id) is None:
        raise ValueError(f"{source} is not a Git blob")
    if re.fullmatch(r"[0-7]{6}", mode) is None:
        raise ValueError(f"{source} returned an invalid Git mode")
    return mode, object_id


def read_tracked_private_gitignore_sentinel(root: Path) -> bytes:
    """Read the exact tracked private sentinel from the current Git commit."""

    try:
        root_path = Path(root).resolve(strict=True)
    except (OSError, ValueError):
        raise ValueError("private sentinel Git root is unavailable") from None
    if not root_path.is_dir():
        raise ValueError("private sentinel Git root is unavailable")

    try:
        head_content = _run_git_bytes(
            root_path,
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        )
        head_lines = head_content.decode(
            "ascii",
            errors="strict",
        ).splitlines()
    except (UnicodeError, ValueError):
        raise ValueError("private sentinel HEAD is unavailable") from None
    if (
        len(head_lines) != 1
        or re.fullmatch(r"[0-9a-f]{40}", head_lines[0]) is None
    ):
        raise ValueError("private sentinel HEAD is unavailable")
    head_commit = head_lines[0]

    try:
        tree_record = _run_git_bytes(
            root_path,
            "ls-tree",
            "-z",
            head_commit,
            "--",
            f":(literal){PRIVATE_GITIGNORE_SENTINEL_RELATIVE_PATH}",
        )
        mode, object_id = _parse_git_object_record(
            tree_record,
            expected_path=PRIVATE_GITIGNORE_SENTINEL_RELATIVE_PATH,
            source="private sentinel Git tree entry",
        )
    except ValueError:
        raise ValueError(
            "private sentinel Git tree entry is missing or ambiguous"
        ) from None
    if mode not in {"100644", "100755"}:
        raise ValueError(
            "private sentinel Git tree entry is not a regular blob"
        )

    try:
        return _run_git_bytes(
            root_path,
            "cat-file",
            "blob",
            object_id,
        )
    except ValueError:
        raise ValueError("private sentinel Git blob is unavailable") from None


def _tree_file_bytes(
    root: Path,
    commit: str,
    relative_path: str,
) -> tuple[str, bytes]:
    record = _run_git_bytes(
        root,
        "ls-tree",
        "-z",
        commit,
        "--",
        f":(literal){relative_path}",
    )
    mode, object_id = _parse_git_object_record(
        record,
        expected_path=relative_path,
        source=f"tree path {commit}:{relative_path}",
    )
    return mode, _run_git_bytes(root, "cat-file", "blob", object_id)


def _index_file_bytes(
    root: Path,
    relative_path: str,
    *,
    required: bool = True,
) -> tuple[str, bytes] | None:
    content = _run_git_bytes(
        root,
        "ls-files",
        "--stage",
        "-z",
        "--",
        f":(literal){relative_path}",
    )
    records = [record for record in content.split(b"\0") if record]
    stage_zero_records: list[bytes] = []
    for record in records:
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_id, stage_number = metadata.decode(
                "ascii",
                errors="strict",
            ).split(" ", 2)
        except (UnicodeError, ValueError) as exc:
            raise ValueError("Git index returned an invalid object record") from exc
        if _canonical_git_path(raw_path) != relative_path:
            raise ValueError("Git index returned a different path")
        if stage_number == "0":
            if re.fullmatch(r"[0-7]{6}", mode) is None:
                raise ValueError("Git index returned an invalid mode")
            if re.fullmatch(r"[0-9a-f]{40,64}", object_id) is None:
                raise ValueError("Git index returned an invalid object ID")
            stage_zero_records.append(record)
    if not stage_zero_records:
        if required:
            raise ValueError(f"Git index does not contain: {relative_path}")
        return None
    if len(stage_zero_records) != 1:
        raise ValueError(f"Git index has an unresolved conflict: {relative_path}")
    metadata = stage_zero_records[0].split(b"\t", 1)[0].decode("ascii")
    mode, object_id, _stage_number = metadata.split(" ", 2)
    return mode, _run_git_bytes(root, "cat-file", "blob", object_id)


def _worktree_file_bytes(root: Path, relative_path: str) -> tuple[str, bytes]:
    candidate = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved_parent = candidate.parent.resolve(strict=True)
        resolved_parent.relative_to(root)
        file_stat = candidate.lstat()
    except FileNotFoundError as exc:
        raise ValueError(f"worktree path does not exist: {relative_path}") from exc
    except (OSError, ValueError) as exc:
        raise ValueError(f"worktree path escapes repository root: {relative_path}") from exc

    if stat.S_ISLNK(file_stat.st_mode):
        try:
            target = os.readlink(candidate)
        except OSError as exc:
            raise ValueError(
                f"worktree symlink could not be read: {relative_path}"
            ) from exc
        return "120000", os.fsencode(target)
    if not stat.S_ISREG(file_stat.st_mode):
        raise ValueError(f"worktree path is not a regular file: {relative_path}")
    try:
        resolved_path = candidate.resolve(strict=True)
        resolved_path.relative_to(root)
        content = resolved_path.read_bytes()
    except (OSError, ValueError) as exc:
        raise ValueError(f"worktree path escapes repository root: {relative_path}") from exc

    index_entry = _index_file_bytes(root, relative_path, required=False)
    if index_entry is not None:
        mode = index_entry[0]
        if os.name != "nt" and mode in {"100644", "100755"}:
            mode = "100755" if file_stat.st_mode & stat.S_IXUSR else "100644"
    else:
        mode = "100755" if file_stat.st_mode & stat.S_IXUSR else "100644"
    return mode, content


def _byte_inventory_entry(
    *,
    relative_path: str,
    mode: str,
    content: bytes,
    git_state: str | None = None,
) -> dict[str, str]:
    entry = {
        "path": relative_path,
        "git_mode": mode,
        "sha256": sha256_bytes(content),
    }
    if git_state is not None:
        entry["git_state"] = git_state
    return entry


def build_git_change_inventories(
    root: Path,
    baseline_commit: str,
    head_commit: str,
) -> dict[str, list[dict[str, str]]]:
    """Bind committed, staged, unstaged, and untracked states to exact bytes."""

    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("Git inventory root must be a directory")
    baseline = _validate_git_commit(
        root_path,
        baseline_commit,
        label="baseline_commit",
    )
    head = _validate_git_commit(root_path, head_commit, label="head_commit")

    committed_changes = _parse_git_name_status_z(
        _run_git_bytes(
            root_path,
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            f"{baseline}..{head}",
            "--",
        )
    )
    staged_changes = _parse_git_name_status_z(
        _run_git_bytes(
            root_path,
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--find-renames",
            head,
            "--",
        )
    )
    unstaged_changes = _parse_git_name_status_z(
        _run_git_bytes(
            root_path,
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "--",
        )
    )
    untracked_paths = [
        _canonical_git_path(raw_path)
        for raw_path in _run_git_bytes(
            root_path,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
        ).split(b"\0")
        if raw_path
    ]

    private_change_paths = sorted({
        relative_path
        for changes in (
            committed_changes,
            staged_changes,
            unstaged_changes,
        )
        for _status, paths in changes
        for relative_path in paths
        if _is_private_relative_path(relative_path)
    } | {
        relative_path
        for relative_path in untracked_paths
        if _is_private_relative_path(relative_path)
    })
    if private_change_paths:
        raise ValueError(
            "Git inventory path targets a private data boundary: "
            f"{private_change_paths[0]}"
        )

    committed_entries: dict[str, dict[str, str]] = {}

    def add_committed(
        relative_path: str,
        source_commit: str,
    ) -> None:
        if _is_output_excluded(relative_path):
            return
        mode, content = _tree_file_bytes(
            root_path,
            source_commit,
            relative_path,
        )
        entry = _byte_inventory_entry(
            relative_path=relative_path,
            mode=mode,
            content=content,
        )
        existing = committed_entries.get(relative_path)
        if existing is not None and existing != entry:
            raise ValueError(
                f"committed inventory contains conflicting bytes: {relative_path}"
            )
        committed_entries[relative_path] = entry

    for status, paths in committed_changes:
        status_code = status[0]
        if status_code in {"R", "C"}:
            old_path, new_path = paths
            add_committed(old_path, baseline)
            add_committed(new_path, head)
        elif status_code == "D":
            add_committed(paths[0], baseline)
        else:
            add_committed(paths[0], head)

    uncommitted_entries: dict[tuple[str, str], dict[str, str]] = {}

    def add_uncommitted(
        relative_path: str,
        git_state: str,
        byte_source: str,
    ) -> None:
        if _is_output_excluded(relative_path):
            return
        if git_state not in {"staged", "unstaged", "untracked"}:
            raise ValueError(f"unsupported uncommitted Git state: {git_state}")
        if byte_source == "head":
            mode, content = _tree_file_bytes(root_path, head, relative_path)
        elif byte_source == "index":
            index_entry = _index_file_bytes(root_path, relative_path)
            if index_entry is None:
                raise ValueError(f"Git index does not contain: {relative_path}")
            mode, content = index_entry
        elif byte_source == "worktree":
            mode, content = _worktree_file_bytes(root_path, relative_path)
        else:
            raise ValueError(f"unsupported inventory byte source: {byte_source}")
        entry = _byte_inventory_entry(
            relative_path=relative_path,
            git_state=git_state,
            mode=mode,
            content=content,
        )
        key = (relative_path, git_state)
        existing = uncommitted_entries.get(key)
        if existing is not None and existing != entry:
            raise ValueError(
                f"uncommitted inventory contains conflicting bytes: "
                f"{relative_path} ({git_state})"
            )
        uncommitted_entries[key] = entry

    for status, paths in staged_changes:
        status_code = status[0]
        if status_code in {"R", "C"}:
            old_path, new_path = paths
            add_uncommitted(old_path, "staged", "head")
            add_uncommitted(new_path, "staged", "index")
        elif status_code == "D":
            add_uncommitted(paths[0], "staged", "head")
        else:
            add_uncommitted(paths[0], "staged", "index")

    for status, paths in unstaged_changes:
        status_code = status[0]
        if status_code in {"R", "C"}:
            old_path, new_path = paths
            add_uncommitted(old_path, "unstaged", "index")
            add_uncommitted(new_path, "unstaged", "worktree")
        elif status_code == "D":
            add_uncommitted(paths[0], "unstaged", "index")
        else:
            add_uncommitted(paths[0], "unstaged", "worktree")

    for relative_path in untracked_paths:
        add_uncommitted(relative_path, "untracked", "worktree")

    return {
        "committed_change_inventory": [
            committed_entries[path]
            for path in sorted(committed_entries)
        ],
        "uncommitted_change_inventory": [
            uncommitted_entries[key]
            for key in sorted(uncommitted_entries)
        ],
    }


def _normalized_repository_paths(
    paths: Sequence[str],
    *,
    label: str,
) -> tuple[str, ...]:
    if isinstance(paths, (str, bytes)) or not isinstance(paths, Sequence):
        raise ValueError(f"{label} must be a sequence")
    normalized_paths: list[str] = []
    seen_paths: set[str] = set()
    for supplied_path in paths:
        normalized_path = _normalize_relative_path(
            supplied_path,
            label=label,
            allow_dot=False,
        )
        if _is_private_relative_path(normalized_path):
            raise ValueError(f"{label} targets a private data boundary")
        if normalized_path in seen_paths:
            raise ValueError(f"{label} contains a duplicate path: {normalized_path}")
        seen_paths.add(normalized_path)
        normalized_paths.append(normalized_path)
    return tuple(sorted(normalized_paths))


def _repository_candidate_kind(
    root: Path,
    relative_path: str,
) -> str | None:
    if _is_private_relative_path(relative_path):
        raise ValueError("dependency path targets a private data boundary")
    candidate = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved_candidate = candidate.resolve(strict=True)
    except FileNotFoundError:
        try:
            unresolved_candidate = candidate.resolve(strict=False)
            unresolved_candidate.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"dependency path escape: {relative_path}"
            ) from exc
        return None
    except OSError as exc:
        raise ValueError(f"dependency path could not be resolved: {relative_path}") from exc
    try:
        resolved_candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"dependency path escape: {relative_path}") from exc
    if resolved_candidate.is_file():
        return "file"
    if resolved_candidate.is_dir():
        return "directory"
    return "other"


def _module_resolution(
    root: Path,
    module_name: str,
) -> tuple[tuple[str, ...], bool]:
    module_parts = module_name.split(".")
    if not module_name or any(
        not part or not part.isidentifier()
        for part in module_parts
    ):
        raise ValueError(f"invalid Python import target: {module_name}")

    initializer_paths: list[str] = []
    for index in range(1, len(module_parts)):
        package_path = "/".join(module_parts[:index])
        initializer_path = f"{package_path}/__init__.py"
        initializer_kind = _repository_candidate_kind(root, initializer_path)
        if initializer_kind == "file":
            initializer_paths.append(initializer_path)
        elif initializer_kind not in {None, "other"}:
            raise ValueError(
                f"local import initializer is not a file: {initializer_path}"
            )

    module_path = "/".join(module_parts) + ".py"
    package_initializer_path = (
        "/".join(module_parts) + "/__init__.py"
    )
    module_kind = _repository_candidate_kind(root, module_path)
    package_initializer_kind = _repository_candidate_kind(
        root,
        package_initializer_path,
    )
    namespace_kind = _repository_candidate_kind(
        root,
        "/".join(module_parts),
    )

    concrete_targets = [
        path
        for path, kind in (
            (module_path, module_kind),
            (package_initializer_path, package_initializer_kind),
        )
        if kind == "file"
    ]
    if len(concrete_targets) > 1:
        raise ValueError(f"ambiguous local import: {module_name}")
    if concrete_targets:
        resolved_paths = tuple(
            dict.fromkeys([*initializer_paths, concrete_targets[0]])
        )
        return resolved_paths, True
    if namespace_kind == "directory":
        return tuple(dict.fromkeys(initializer_paths)), True
    return (), False


def _top_level_module_is_local(root: Path, module_name: str) -> bool:
    top_level_name = module_name.split(".", 1)[0]
    module_kind = _repository_candidate_kind(root, f"{top_level_name}.py")
    package_kind = _repository_candidate_kind(root, top_level_name)
    return module_kind == "file" or package_kind == "directory"


def _consumer_package_parts(relative_path: str) -> list[str]:
    path = PurePosixPath(relative_path)
    parent_parts = list(path.parent.parts)
    if path.name == "__init__.py":
        return parent_parts
    return parent_parts


def _relative_import_base(
    consumer_path: str,
    *,
    level: int,
    module: str | None,
) -> str:
    package_parts = _consumer_package_parts(consumer_path)
    if level < 1 or level > len(package_parts):
        raise ValueError(
            f"relative import path escape in {consumer_path}"
        )
    retained_parts = package_parts[: len(package_parts) - level + 1]
    if module:
        retained_parts.extend(module.split("."))
    if not retained_parts:
        raise ValueError(
            f"relative import path escape in {consumer_path}"
        )
    return ".".join(retained_parts)


def _forbidden_import_prefix(
    module_name: str,
    forbidden_import_prefixes: tuple[str, ...],
) -> str | None:
    for prefix in forbidden_import_prefixes:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return prefix
    return None


def _guard_allows_socket_import(
    consumer_path: str,
    module_name: str,
    guard_implementation_path: str,
) -> bool:
    return (
        consumer_path == guard_implementation_path
        and (
            module_name == "socket"
            or module_name.startswith("socket.")
        )
    )


def _resolve_import_node(
    *,
    root: Path,
    consumer_path: str,
    node: ast.Import | ast.ImportFrom,
    forbidden_import_prefixes: tuple[str, ...],
    guard_implementation_path: str,
) -> set[str]:
    dependencies: set[str] = set()

    def reject_forbidden(module_name: str) -> None:
        prefix = _forbidden_import_prefix(
            module_name,
            forbidden_import_prefixes,
        )
        if prefix is not None and not _guard_allows_socket_import(
            consumer_path,
            module_name,
            guard_implementation_path,
        ):
            raise ValueError(
                f"forbidden import in {consumer_path}: {module_name}"
            )

    if isinstance(node, ast.Import):
        for alias in node.names:
            module_name = alias.name
            reject_forbidden(module_name)
            resolved_paths, resolved_locally = _module_resolution(
                root,
                module_name,
            )
            if resolved_locally:
                dependencies.update(resolved_paths)
            elif _top_level_module_is_local(root, module_name):
                raise ValueError(
                    f"unresolved local import in {consumer_path}: {module_name}"
                )
        return dependencies

    if node.level:
        base_module = _relative_import_base(
            consumer_path,
            level=node.level,
            module=node.module,
        )
        relative_import = True
    else:
        base_module = node.module or ""
        relative_import = False
        if base_module:
            reject_forbidden(base_module)

    for alias in node.names:
        full_module = (
            base_module
            if alias.name == "*"
            else f"{base_module}.{alias.name}" if base_module else alias.name
        )
        if not relative_import:
            reject_forbidden(full_module)
        full_paths, full_is_local = _module_resolution(root, full_module)
        if full_is_local and full_paths:
            dependencies.update(full_paths)
            continue

        base_paths: tuple[str, ...] = ()
        base_is_local = False
        if base_module:
            base_paths, base_is_local = _module_resolution(root, base_module)
        if base_is_local:
            dependencies.update(base_paths)
            continue
        if relative_import or _top_level_module_is_local(root, full_module):
            raise ValueError(
                f"unresolved local import in {consumer_path}: {full_module}"
            )
    return dependencies


_SUBPROCESS_FUNCTION_NAMES = {
    "call",
    "check_call",
    "check_output",
    "Popen",
    "run",
}
_REVIEWED_INLINE_PYTHON_CONSUMERS = frozenset(
    {
        "scripts/test_emotion_state_001_closeout_hardening.py",
        "scripts/test_emotion_state_001_open_dataset_gate.py",
    }
)


def _subprocess_aliases(
    tree: ast.AST,
) -> tuple[set[str], set[str], set[str], set[str]]:
    subprocess_modules: set[str] = set()
    subprocess_functions: set[str] = set()
    sys_modules: set[str] = set()
    sys_executables: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    subprocess_modules.add(alias.asname or alias.name)
                elif alias.name == "sys":
                    sys_modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module == "subprocess":
                for alias in node.names:
                    if alias.name in _SUBPROCESS_FUNCTION_NAMES:
                        subprocess_functions.add(alias.asname or alias.name)
            elif node.level == 0 and node.module == "sys":
                for alias in node.names:
                    if alias.name == "executable":
                        sys_executables.add(alias.asname or alias.name)
    return (
        subprocess_modules,
        subprocess_functions,
        sys_modules,
        sys_executables,
    )


def _is_subprocess_call(
    function: ast.expr,
    *,
    subprocess_modules: set[str],
    subprocess_functions: set[str],
) -> bool:
    if isinstance(function, ast.Name):
        return function.id in subprocess_functions
    return (
        isinstance(function, ast.Attribute)
        and function.attr in _SUBPROCESS_FUNCTION_NAMES
        and isinstance(function.value, ast.Name)
        and function.value.id in subprocess_modules
    )


def _is_python_executable_expression(
    expression: ast.expr,
    *,
    sys_modules: set[str],
    sys_executables: set[str],
) -> bool:
    if isinstance(expression, ast.Name):
        return expression.id in sys_executables
    if (
        isinstance(expression, ast.Attribute)
        and expression.attr == "executable"
        and isinstance(expression.value, ast.Name)
        and expression.value.id in sys_modules
    ):
        return True
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        executable_name = PureWindowsPath(expression.value).name.casefold()
        return executable_name in {
            "py",
            "py.exe",
            "python",
            "python.exe",
            "python3",
            "python3.exe",
        }
    return False


def _literal_string(expression: ast.expr) -> str | None:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    return None


def _static_repository_path_resolver(
    tree: ast.AST,
    *,
    consumer_path: str,
) -> Callable[[ast.expr], str | None]:
    assignments: dict[str, list[ast.expr | None]] = {}
    pathlib_path_names: set[str] = set()
    pathlib_module_names: set[str] = set()

    def add_assignment(name: str, value: ast.expr | None) -> None:
        assignments.setdefault(name, []).append(value)

    def mark_bound_target(target: ast.expr) -> None:
        if isinstance(target, ast.Name):
            add_assignment(target.id, None)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                mark_bound_target(element)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pathlib":
                    pathlib_module_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module == "pathlib":
                for alias in node.names:
                    if alias.name == "Path":
                        pathlib_path_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    add_assignment(target.id, node.value)
                else:
                    mark_bound_target(target)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                add_assignment(node.target.id, node.value)
            else:
                mark_bound_target(node.target)
        elif isinstance(node, ast.NamedExpr):
            if isinstance(node.target, ast.Name):
                add_assignment(node.target.id, node.value)
        elif isinstance(node, ast.AugAssign):
            mark_bound_target(node.target)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            mark_bound_target(node.target)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    mark_bound_target(item.optional_vars)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            add_assignment(node.name, None)
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
        ):
            arguments = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            if node.args.vararg is not None:
                arguments.append(node.args.vararg)
            if node.args.kwarg is not None:
                arguments.append(node.args.kwarg)
            for argument in arguments:
                add_assignment(argument.arg, None)

    resolved_names: dict[str, PurePosixPath | None] = {}
    resolving_names: set[str] = set()

    def normalize_path_fragment(value: str) -> tuple[str, ...]:
        if (
            not value
            or "\x00" in value
            or PureWindowsPath(value).drive
            or PureWindowsPath(value).root
        ):
            raise ValueError(f"subprocess target path escape: {value}")
        fragment = PurePosixPath(value.replace("\\", "/"))
        if fragment.is_absolute() or ".." in fragment.parts:
            raise ValueError(f"subprocess target path escape: {value}")
        return tuple(part for part in fragment.parts if part != ".")

    def resolve_name(name: str) -> PurePosixPath | None:
        if name in resolved_names:
            return resolved_names[name]
        if name in resolving_names:
            return None
        expressions = assignments.get(name)
        if not expressions:
            return None
        resolving_names.add(name)
        values: list[PurePosixPath] = []
        for expression in expressions:
            if expression is None:
                resolving_names.remove(name)
                resolved_names[name] = None
                return None
            value = resolve_expression(expression)
            if value is None:
                resolving_names.remove(name)
                resolved_names[name] = None
                return None
            values.append(value)
        resolving_names.remove(name)
        if not values or any(value != values[0] for value in values[1:]):
            resolved_names[name] = None
            return None
        resolved_names[name] = values[0]
        return values[0]

    def is_path_constructor(function: ast.expr) -> bool:
        if isinstance(function, ast.Name):
            return function.id in pathlib_path_names
        return (
            isinstance(function, ast.Attribute)
            and function.attr == "Path"
            and isinstance(function.value, ast.Name)
            and function.value.id in pathlib_module_names
        )

    def resolve_expression(expression: ast.expr) -> PurePosixPath | None:
        if isinstance(expression, ast.Name):
            if expression.id == "__file__" and "__file__" not in assignments:
                return PurePosixPath(consumer_path)
            return resolve_name(expression.id)
        if (
            isinstance(expression, ast.Call)
            and is_path_constructor(expression.func)
            and len(expression.args) == 1
            and not expression.keywords
        ):
            return resolve_expression(expression.args[0])
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id == "str"
            and "str" not in assignments
            and len(expression.args) == 1
            and not expression.keywords
        ):
            return resolve_expression(expression.args[0])
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Attribute)
            and expression.func.attr == "resolve"
            and not expression.args
            and not expression.keywords
        ):
            return resolve_expression(expression.func.value)
        if (
            isinstance(expression, ast.Attribute)
            and expression.attr == "parent"
        ):
            base_path = resolve_expression(expression.value)
            return None if base_path is None else base_path.parent
        if (
            isinstance(expression, ast.Subscript)
            and isinstance(expression.value, ast.Attribute)
            and expression.value.attr == "parents"
            and isinstance(expression.slice, ast.Constant)
            and type(expression.slice.value) is int
            and expression.slice.value >= 0
        ):
            base_path = resolve_expression(expression.value.value)
            if base_path is None:
                return None
            try:
                return base_path.parents[expression.slice.value]
            except IndexError:
                return None
        if (
            isinstance(expression, ast.BinOp)
            and isinstance(expression.op, ast.Div)
        ):
            base_path = resolve_expression(expression.left)
            path_fragment = _literal_string(expression.right)
            if base_path is None or path_fragment is None:
                return None
            return base_path.joinpath(*normalize_path_fragment(path_fragment))
        return None

    def resolve_target(expression: ast.expr) -> str | None:
        resolved_path = resolve_expression(expression)
        if resolved_path is None:
            return None
        normalized_path = resolved_path.as_posix()
        if normalized_path == ".":
            return None
        return _normalize_relative_path(
            normalized_path,
            label="statically resolved Python subprocess target",
            allow_dot=False,
        )

    return resolve_target


def _resolve_subprocess_file_target(
    root: Path,
    target: str,
) -> str:
    try:
        normalized_target = _normalize_relative_path(
            target,
            label="Python subprocess target",
            allow_dot=False,
        )
    except ValueError as exc:
        raise ValueError(f"subprocess target path escape: {target}") from exc
    if _is_private_relative_path(normalized_target):
        raise ValueError("Python subprocess target is inside a private data boundary")
    target_kind = _repository_candidate_kind(root, normalized_target)
    if target_kind != "file":
        raise ValueError(
            f"unresolved Python subprocess target: {normalized_target}"
        )
    return normalized_target


def _resolve_subprocess_module_target(
    root: Path,
    module_name: str,
) -> str:
    resolved_paths, resolved_locally = _module_resolution(root, module_name)
    if not resolved_locally or not resolved_paths:
        raise ValueError(
            f"unresolved Python subprocess target: {module_name}"
        )
    return resolved_paths[-1]


def _resolve_python_subprocess_calls(
    *,
    root: Path,
    consumer_path: str,
    tree: ast.AST,
) -> set[str]:
    (
        subprocess_modules,
        subprocess_functions,
        sys_modules,
        sys_executables,
    ) = _subprocess_aliases(tree)
    resolve_static_path = _static_repository_path_resolver(
        tree,
        consumer_path=consumer_path,
    )
    dependencies: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_subprocess_call(
            node.func,
            subprocess_modules=subprocess_modules,
            subprocess_functions=subprocess_functions,
        ):
            continue
        argv_expression: ast.expr | None = node.args[0] if node.args else None
        if argv_expression is None:
            for keyword in node.keywords:
                if keyword.arg == "args":
                    argv_expression = keyword.value
                    break
        if not isinstance(argv_expression, (ast.List, ast.Tuple)):
            continue
        argv_elements = list(argv_expression.elts)
        if not argv_elements:
            continue
        if not _is_python_executable_expression(
            argv_elements[0],
            sys_modules=sys_modules,
            sys_executables=sys_executables,
        ):
            later_literals = [
                value
                for value in (
                    _literal_string(element)
                    for element in argv_elements[1:]
                )
                if value is not None
            ]
            if "-m" in later_literals or any(
                value.casefold().endswith(".py")
                for value in later_literals
            ):
                raise ValueError(
                    f"dynamic subprocess target in {consumer_path}"
                )
            continue

        arguments = argv_elements[1:]
        argument_index = 0
        while argument_index < len(arguments):
            argument_expression = arguments[argument_index]
            literal_argument = _literal_string(argument_expression)
            if literal_argument is None:
                static_target = resolve_static_path(argument_expression)
                if static_target is None:
                    raise ValueError(
                        f"dynamic subprocess target in {consumer_path}"
                    )
                dependencies.add(
                    _resolve_subprocess_file_target(root, static_target)
                )
                break
            if literal_argument == "-m":
                if argument_index + 1 >= len(arguments):
                    raise ValueError(
                        f"dynamic subprocess target in {consumer_path}"
                    )
                module_name = _literal_string(arguments[argument_index + 1])
                if module_name is None:
                    raise ValueError(
                        f"dynamic subprocess target in {consumer_path}"
                    )
                dependencies.add(
                    _resolve_subprocess_module_target(root, module_name)
                )
                break
            if literal_argument == "-c":
                if (
                    consumer_path not in _REVIEWED_INLINE_PYTHON_CONSUMERS
                    or argument_index + 1 >= len(arguments)
                ):
                    raise ValueError(
                        f"dynamic subprocess target in {consumer_path}"
                    )
                break
            if literal_argument in {"-W", "-X"}:
                argument_index += 2
                continue
            if literal_argument.startswith("-"):
                argument_index += 1
                continue
            dependencies.add(
                _resolve_subprocess_file_target(root, literal_argument)
            )
            break
        else:
            raise ValueError(
                f"dynamic subprocess target in {consumer_path}"
            )
    return dependencies


def _closure_file_entry(
    root: Path,
    relative_path: str,
) -> tuple[dict[str, str], bytes]:
    path_kind = _repository_candidate_kind(root, relative_path)
    if path_kind != "file":
        raise ValueError(f"executable dependency is not a file: {relative_path}")
    mode, content = _worktree_file_bytes(root, relative_path)
    return (
        _byte_inventory_entry(
            relative_path=relative_path,
            mode=mode,
            content=content,
        ),
        content,
    )


def _runtime_consumer_import_dependencies(
    *,
    root: Path,
    runtime_consumer_path: str,
    guard_implementation_path: str,
) -> set[str]:
    if PurePosixPath(runtime_consumer_path).suffix.casefold() != ".py":
        raise ValueError(
            f"runtime consumer is not a Python file: {runtime_consumer_path}"
        )
    if _index_file_bytes(
        root,
        runtime_consumer_path,
        required=False,
    ) is None:
        raise ValueError(
            f"runtime consumer must be tracked: {runtime_consumer_path}"
        )
    path_kind = _repository_candidate_kind(root, runtime_consumer_path)
    if path_kind != "file":
        raise ValueError(
            f"runtime consumer is not a file: {runtime_consumer_path}"
        )
    _mode, content = _worktree_file_bytes(root, runtime_consumer_path)
    try:
        tree = ast.parse(content, filename=runtime_consumer_path)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(
            f"runtime consumer could not be parsed: {runtime_consumer_path}"
        ) from exc

    dependencies: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            dependencies.update(
                _resolve_import_node(
                    root=root,
                    consumer_path=runtime_consumer_path,
                    node=node,
                    forbidden_import_prefixes=(),
                    guard_implementation_path=guard_implementation_path,
                )
            )
    return dependencies


def build_executable_dependency_closure(
    *,
    root: Path,
    executable_roots: Sequence[str],
    forbidden_import_prefixes: Sequence[str],
    guard_implementation_path: str,
    gate_module_paths: Sequence[str] = (),
    runtime_consumer_paths: Sequence[str] = (),
) -> dict[str, object]:
    """Build an AST-only, byte-bound closure of local Python execution edges."""

    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("dependency closure root must be a directory")
    normalized_roots = _normalized_repository_paths(
        executable_roots,
        label="executable_roots",
    )
    if not normalized_roots:
        raise ValueError("executable_roots must not be empty")
    normalized_guard_path = _normalize_relative_path(
        guard_implementation_path,
        label="guard_implementation_path",
        allow_dot=False,
    )
    if _is_private_relative_path(normalized_guard_path):
        raise ValueError("guard implementation targets a private data boundary")
    normalized_gate_paths = set(
        _normalized_repository_paths(
            gate_module_paths,
            label="gate_module_paths",
        )
    )
    normalized_runtime_paths = set(
        _normalized_repository_paths(
            runtime_consumer_paths,
            label="runtime_consumer_paths",
        )
    )
    if normalized_gate_paths.intersection(normalized_runtime_paths):
        raise ValueError("runtime consumer is also declared as a gate module")

    if isinstance(forbidden_import_prefixes, (str, bytes)) or not isinstance(
        forbidden_import_prefixes,
        Sequence,
    ):
        raise ValueError("forbidden_import_prefixes must be a sequence")
    normalized_forbidden_prefixes: list[str] = []
    seen_forbidden_prefixes: set[str] = set()
    for prefix in forbidden_import_prefixes:
        if (
            not isinstance(prefix, str)
            or not prefix
            or prefix.startswith(".")
            or prefix.endswith(".")
            or any(not part.isidentifier() for part in prefix.split("."))
        ):
            raise ValueError(f"invalid forbidden import prefix: {prefix!r}")
        if prefix in seen_forbidden_prefixes:
            raise ValueError(f"duplicate forbidden import prefix: {prefix}")
        seen_forbidden_prefixes.add(prefix)
        normalized_forbidden_prefixes.append(prefix)
    forbidden_prefixes = tuple(sorted(normalized_forbidden_prefixes))

    for runtime_path in sorted(normalized_runtime_paths):
        runtime_dependencies = _runtime_consumer_import_dependencies(
            root=root_path,
            runtime_consumer_path=runtime_path,
            guard_implementation_path=normalized_guard_path,
        )
        gate_dependencies = sorted(
            runtime_dependencies.intersection(normalized_gate_paths)
        )
        if gate_dependencies:
            raise ValueError(
                f"runtime consumer {runtime_path} imports gate module "
                f"{gate_dependencies[0]}"
            )

    inventory_by_path: dict[str, dict[str, str]] = {}
    edges: set[tuple[str, str, str]] = set()
    pending_paths: set[str] = set(normalized_roots)
    parsed_paths: set[str] = set()

    while pending_paths:
        consumer_path = min(pending_paths)
        pending_paths.remove(consumer_path)
        if consumer_path in parsed_paths:
            continue
        if PurePosixPath(consumer_path).suffix.casefold() != ".py":
            raise ValueError(
                f"executable dependency is not a Python file: {consumer_path}"
            )
        inventory_entry, content = _closure_file_entry(
            root_path,
            consumer_path,
        )
        inventory_by_path[consumer_path] = inventory_entry
        try:
            tree = ast.parse(content, filename=consumer_path)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(
                f"Python executable could not be parsed: {consumer_path}"
            ) from exc

        local_dependencies: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                local_dependencies.update(
                    _resolve_import_node(
                        root=root_path,
                        consumer_path=consumer_path,
                        node=node,
                        forbidden_import_prefixes=forbidden_prefixes,
                        guard_implementation_path=normalized_guard_path,
                    )
                )
        for dependency_path in sorted(local_dependencies):
            if dependency_path == consumer_path:
                continue
            edges.add(
                (consumer_path, dependency_path, "python_import")
            )
            pending_paths.add(dependency_path)

        subprocess_dependencies = _resolve_python_subprocess_calls(
            root=root_path,
            consumer_path=consumer_path,
            tree=tree,
        )
        for dependency_path in sorted(subprocess_dependencies):
            if dependency_path == consumer_path:
                continue
            edges.add(
                (
                    consumer_path,
                    dependency_path,
                    "python_subprocess_target",
                )
            )
            pending_paths.add(dependency_path)
        parsed_paths.add(consumer_path)

    inventory = [
        inventory_by_path[path]
        for path in sorted(inventory_by_path)
    ]
    edge_inventory = [
        {
            "consumer": consumer,
            "dependency": dependency,
            "edge_type": edge_type,
        }
        for consumer, dependency, edge_type in sorted(edges)
    ]
    digest_payload = json.dumps(
        {
            "edges": edge_inventory,
            "inventory": inventory,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "inventory": inventory,
        "edges": edge_inventory,
        "digest": sha256_bytes(digest_payload),
    }


def _validate_evidence_commit(value: str, *, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError(f"{label} must be a lowercase 40-hex commit")
    return value


def _tracked_runtime_python_paths(root: Path) -> tuple[str, ...]:
    tracked_paths = {
        _canonical_git_path(raw_path)
        for raw_path in _run_git_bytes(
            root,
            "ls-files",
            "-z",
            "--",
            "runtime",
        ).split(b"\0")
        if raw_path
    }
    return tuple(
        sorted(
            path
            for path in tracked_paths
            if path.startswith("runtime/")
            and PurePosixPath(path).suffix.casefold() == ".py"
        )
    )


def _materializable_changed_python_paths(
    root: Path,
    inventories: Mapping[str, object],
) -> tuple[str, ...]:
    changed_paths: set[str] = set()
    for inventory_name in (
        "committed_change_inventory",
        "uncommitted_change_inventory",
    ):
        inventory = inventories.get(inventory_name)
        if not isinstance(inventory, list):
            raise ValueError(f"{inventory_name} must be a list")
        for entry in inventory:
            if not isinstance(entry, Mapping):
                raise ValueError(f"{inventory_name} entry must be a mapping")
            relative_path = entry.get("path")
            if not isinstance(relative_path, str):
                raise ValueError(f"{inventory_name} path must be text")
            if PurePosixPath(relative_path).suffix.casefold() != ".py":
                continue
            if _repository_candidate_kind(root, relative_path) == "file":
                changed_paths.add(relative_path)
    return tuple(sorted(changed_paths))


def _collect_verification_snapshot(
    *,
    root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> dict[str, object]:
    """Collect only byte-bound repository inputs for a verification run."""

    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("verification snapshot root must be a directory")
    baseline = _validate_evidence_commit(
        baseline_commit,
        label="baseline_commit",
    )
    head = _validate_evidence_commit(head_commit, label="head_commit")
    if mode != "material-pending":
        raise ValueError(
            "complete verification snapshot requires authorized dataset evidence"
        )

    inventories = build_git_change_inventories(root_path, baseline, head)
    executable_roots = set(REVIEWED_EXECUTABLE_ROOTS)
    executable_roots.update(
        _materializable_changed_python_paths(root_path, inventories)
    )
    if (
        _repository_candidate_kind(
            root_path,
            GUARD_IMPLEMENTATION_RELATIVE_PATH,
        )
        == "file"
    ):
        executable_roots.add(GUARD_IMPLEMENTATION_RELATIVE_PATH)

    closure = build_executable_dependency_closure(
        root=root_path,
        executable_roots=tuple(sorted(executable_roots)),
        forbidden_import_prefixes=FORBIDDEN_IMPORT_PREFIXES,
        guard_implementation_path=GUARD_IMPLEMENTATION_RELATIVE_PATH,
        gate_module_paths=GATE_MODULE_PATHS,
        runtime_consumer_paths=_tracked_runtime_python_paths(root_path),
    )
    return {
        "committed_change_inventory": inventories[
            "committed_change_inventory"
        ],
        "uncommitted_change_inventory": inventories[
            "uncommitted_change_inventory"
        ],
        "executable_dependency_closure": closure,
        "dataset_manifest_digests": {},
        "dataset_hash_inventory_digests": {},
    }


def _execute_guarded_commands(
    *,
    root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> list[dict[str, object]]:
    """Execute the exact policy command sequence through the guarded launcher."""

    root_path = Path(root).resolve(strict=True)
    baseline = _validate_evidence_commit(
        baseline_commit,
        label="baseline_commit",
    )
    head = _validate_evidence_commit(head_commit, label="head_commit")
    command_runner = globals().get("run_guarded_command")
    if not callable(command_runner):
        raise RuntimeError("run_guarded_command is not implemented")

    available_substitutions = {
        "baseline_commit": baseline,
        "head_commit": head,
        "mode": mode,
    }
    ledger: list[dict[str, object]] = []
    for sequence_number, (command_id, argv_template) in enumerate(
        _expected_mode_commands(mode),
        start=1,
    ):
        required_substitutions = {
            substitution
            for argument in argv_template
            for substitution in re.findall(r"\{([a-z_]+)\}", argument)
        }
        entry = command_runner(
            command_id,
            root_path,
            {
                name: available_substitutions[name]
                for name in sorted(required_substitutions)
            },
        )
        if not isinstance(entry, Mapping):
            raise ValueError("guarded command result must be a mapping")
        ledger.append(
            canonical_command_entry(
                sequence_number=sequence_number,
                command_id=entry.get("command_id"),
                argv=entry.get("argv"),
                working_directory=entry.get("working_directory"),
                exit_status=entry.get("exit_status"),
            )
        )
    return ledger


@contextmanager
def publication_lock(*, recovery_dir: Path) -> Iterator[Path]:
    """Hold the deterministic publication mutex for one locked re-read."""

    recovery_path = Path(recovery_dir)
    try:
        recovery_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(
            "unable to prepare verification publication recovery directory"
        ) from exc
    lock_path = recovery_path / PUBLICATION_LOCK_NAME
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except FileExistsError as exc:
        raise ValueError("verification publication lock is already held") from exc
    except OSError as exc:
        raise ValueError("unable to acquire verification publication lock") from exc
    try:
        yield lock_path
    finally:
        try:
            os.close(descriptor)
        finally:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _read_validated_guard_policy_bytes(root: Path) -> bytes:
    policy_path = root / GUARD_POLICY_RELATIVE_PATH
    try:
        policy_bytes = policy_path.read_bytes()
    except OSError as exc:
        raise ValueError(
            "guard policy could not be read from verification root"
        ) from exc
    policy = _load_json_bytes(policy_bytes, source="guard policy")
    _assert_exact_policy_value(policy, EXPECTED_GUARD_POLICY, location="$")
    return policy_bytes


def _verification_snapshot_components(
    snapshot: Mapping[str, object],
) -> tuple[
    list[object],
    list[object],
    list[object],
    list[object],
    Mapping[str, object],
    Mapping[str, object],
]:
    expected_fields = {
        "committed_change_inventory",
        "uncommitted_change_inventory",
        "executable_dependency_closure",
        "dataset_manifest_digests",
        "dataset_hash_inventory_digests",
    }
    if not isinstance(snapshot, Mapping) or set(snapshot) != expected_fields:
        raise ValueError("verification snapshot fields mismatch")
    committed_inventory = snapshot["committed_change_inventory"]
    uncommitted_inventory = snapshot["uncommitted_change_inventory"]
    closure = snapshot["executable_dependency_closure"]
    manifest_digests = snapshot["dataset_manifest_digests"]
    hash_inventory_digests = snapshot["dataset_hash_inventory_digests"]
    if not isinstance(committed_inventory, list):
        raise ValueError("committed change inventory must be a list")
    if not isinstance(uncommitted_inventory, list):
        raise ValueError("uncommitted change inventory must be a list")
    if not isinstance(closure, Mapping) or set(closure) != {
        "inventory",
        "edges",
        "digest",
    }:
        raise ValueError("executable dependency closure fields mismatch")
    closure_inventory = closure["inventory"]
    closure_edges = closure["edges"]
    if not isinstance(closure_inventory, list):
        raise ValueError("executable dependency closure inventory must be a list")
    if not isinstance(closure_edges, list):
        raise ValueError("executable dependency closure edges must be a list")
    if not isinstance(manifest_digests, Mapping):
        raise ValueError("dataset manifest digests must be a mapping")
    if not isinstance(hash_inventory_digests, Mapping):
        raise ValueError("dataset hash inventory digests must be a mapping")
    return (
        committed_inventory,
        uncommitted_inventory,
        closure_inventory,
        closure_edges,
        manifest_digests,
        hash_inventory_digests,
    )


@dataclass(frozen=True, slots=True, repr=False)
class PreparedVerificationEvidence:
    """In-memory inputs awaiting a caller-controlled locked re-read."""

    baseline_commit: str
    head_commit: str
    mode: str
    initial_policy_bytes: bytes
    initial_snapshot_bytes: bytes
    executed_command_ledger_bytes: bytes


def _validated_verification_request(
    root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> tuple[Path, str, str]:
    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("verification evidence root must be a directory")
    baseline = _validate_evidence_commit(
        baseline_commit,
        label="baseline_commit",
    )
    head = _validate_evidence_commit(head_commit, label="head_commit")
    _expected_mode_commands(mode)
    return root_path, baseline, head


def prepare_verification_evidence(
    root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> PreparedVerificationEvidence:
    """Capture validated initial inputs and the exact guarded-command ledger."""

    root_path, baseline, head = _validated_verification_request(
        root,
        baseline_commit,
        head_commit,
        mode,
    )

    initial_policy_bytes = _read_validated_guard_policy_bytes(root_path)
    initial_snapshot = _collect_verification_snapshot(
        root=root_path,
        baseline_commit=baseline,
        head_commit=head,
        mode=mode,
    )
    executed_command_ledger = _execute_guarded_commands(
        root=root_path,
        baseline_commit=baseline,
        head_commit=head,
        mode=mode,
    )
    return PreparedVerificationEvidence(
        baseline_commit=baseline,
        head_commit=head,
        mode=mode,
        initial_policy_bytes=initial_policy_bytes,
        initial_snapshot_bytes=canonical_json_bytes(initial_snapshot),
        executed_command_ledger_bytes=canonical_json_bytes(
            executed_command_ledger
        ),
    )


def finalize_verification_evidence(
    prepared: PreparedVerificationEvidence,
    *,
    root: Path,
) -> dict[str, object]:
    """Finalize canonical evidence while the caller holds its publication lock."""

    if not isinstance(prepared, PreparedVerificationEvidence):
        raise ValueError("prepared verification evidence is invalid")
    root_path, baseline, head = _validated_verification_request(
        root,
        prepared.baseline_commit,
        prepared.head_commit,
        prepared.mode,
    )
    if (
        not isinstance(prepared.initial_policy_bytes, bytes)
        or not isinstance(prepared.initial_snapshot_bytes, bytes)
        or not isinstance(prepared.executed_command_ledger_bytes, bytes)
    ):
        raise ValueError("prepared verification evidence is invalid")
    initial_policy = _load_json_bytes(
        prepared.initial_policy_bytes,
        source="prepared guard policy",
    )
    _assert_exact_policy_value(initial_policy, EXPECTED_GUARD_POLICY, location="$")
    initial_snapshot = _load_json_bytes(
        prepared.initial_snapshot_bytes,
        source="prepared verification snapshot",
    )
    executed_command_ledger = _load_json_bytes(
        prepared.executed_command_ledger_bytes,
        source="prepared guarded-command ledger",
    )
    if not isinstance(initial_snapshot, Mapping):
        raise ValueError("prepared verification snapshot must be a mapping")
    if not isinstance(executed_command_ledger, list):
        raise ValueError("prepared guarded-command ledger must be a list")

    locked_policy_bytes = _read_validated_guard_policy_bytes(root_path)
    locked_snapshot = _collect_verification_snapshot(
        root=root_path,
        baseline_commit=baseline,
        head_commit=head,
        mode=prepared.mode,
    )
    if (
        prepared.initial_policy_bytes != locked_policy_bytes
        or prepared.initial_snapshot_bytes
        != canonical_json_bytes(locked_snapshot)
    ):
        raise ValueError(
            "verification inputs changed during locked re-read"
        )

    (
        committed_inventory,
        uncommitted_inventory,
        closure_inventory,
        closure_edges,
        manifest_digests,
        hash_inventory_digests,
    ) = _verification_snapshot_components(locked_snapshot)
    ledger = [dict(entry) for entry in executed_command_ledger]
    repository_gate_statuses = derive_repository_gate_statuses(
        ledger,
        prepared.mode,
    )
    guarded_command_results = {
        entry["command_id"]: entry["exit_status"]
        for entry in ledger
    }
    input_inventory_digest = canonical_json_sha256({
        "committed_change_inventory": committed_inventory,
        "uncommitted_change_inventory": uncommitted_inventory,
    })
    closure_digest = canonical_json_sha256({
        "edges": closure_edges,
        "inventory": closure_inventory,
    })
    ledger_digest = canonical_json_sha256(ledger)
    guard_policy_digest = sha256_bytes(locked_policy_bytes)
    tree_payload = {
        "implementation_baseline_commit": baseline,
        "repository_head_commit": head,
        "committed_change_inventory": committed_inventory,
        "uncommitted_change_inventory": uncommitted_inventory,
        "executable_dependency_closure_inventory": closure_inventory,
        "executable_dependency_closure_edges": closure_edges,
        "dataset_manifest_digests": dict(manifest_digests),
        "dataset_hash_inventory_digests": dict(hash_inventory_digests),
        "executed_command_ledger": ledger,
        "guard_policy_digest": guard_policy_digest,
    }
    tree_digest = canonical_json_sha256(tree_payload)
    verification_run_id = sha256_bytes(
        (
            "emotion-state-phase-a-validator-v1:"
            + tree_digest
        ).encode("utf-8")
    )
    return {
        **tree_payload,
        "verification_input_path_inventory_digest": input_inventory_digest,
        "executable_dependency_closure_digest": closure_digest,
        "executed_command_ledger_digest": ledger_digest,
        "verification_input_tree_digest": tree_digest,
        "verification_run_id": verification_run_id,
        "guarded_command_results": guarded_command_results,
        "repository_gate_statuses": repository_gate_statuses,
        "provider_environment_scrubbed": True,
        "private_path_guard_enabled": True,
        "network_guard_enabled": True,
    }


def build_verification_evidence(
    root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> dict[str, object]:
    """Build deterministic evidence only after an unchanged locked re-read."""

    root_path = Path(root).resolve(strict=True)
    prepared = prepare_verification_evidence(
        root_path,
        baseline_commit,
        head_commit,
        mode,
    )
    recovery_dir = root_path.joinpath(
        *PurePosixPath(PUBLICATION_RECOVERY_RELATIVE_PATH).parts
    )
    with publication_lock(recovery_dir=recovery_dir):
        return finalize_verification_evidence(prepared, root=root_path)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the pathless verification-evidence CLI."""

    parser = argparse.ArgumentParser(
        description="Validate derived EMOTION-STATE Phase A verification inputs."
    )
    parser.add_argument(
        "--validate-json-inputs",
        action="store_true",
        help="validate only JSON paths derived by the verification workflow",
    )
    return parser.parse_args(argv)


# Stable private aliases used by later production units in this module.
_canonical_json_bytes = canonical_json_bytes
_sha256_bytes = sha256_bytes
