"""Opt-in fail-closed guards for EMOTION-STATE Phase A verification."""

from __future__ import annotations

import builtins
import hashlib
import inspect
import io
import json
import os
import re
import socket
import stat
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from types import MappingProxyType


_POLICY_DIGEST = (
    "A750C3EB69EB35D100AB32C9DCAFA9E02D2C91BD2BF8BACD6AB7F39899FC0DDE"
)
_POLICY_ID = "emotion-state-phase-a-verification-guard-v1"
_PRIVATE_DENIAL = "EMOTION-STATE Phase A private path access is blocked"
_NETWORK_DENIAL = "EMOTION-STATE Phase A network access is blocked"
_PROCESS_DENIAL = "EMOTION-STATE Phase A process launch is blocked"
_RULE_KINDS = {"python_inline", "python_target", "git"}
_CWD_CLASSES = {"project_root", "transaction_descendant"}
_ENVIRONMENT_CLASSES = {"inherit", "guarded_child", "synthetic_guard"}
_GIT_MATCHER_IDS = {
    "transaction_fixture",
    "transaction_verification",
    "project_root_sentinel",
    "thesis_status",
}
_FIXTURE_COMMIT_MESSAGES = {
    "baseline",
    "closure fixture",
    "missing sentinel fixture",
    "private change",
    "private sentinel fixture",
    "rejection fixture",
    "rename and delete",
    "reviewed SDD fixture",
    "reviewed subprocess fixtures",
    "runtime consumer gate fixtures",
    "tracked private fixture",
}
_LOWER_HEX_40_RE = re.compile(r"[0-9a-f]{40}")
_LOWER_HEX_OBJECT_RE = re.compile(r"[0-9a-f]{40,64}")
_UPPER_SHA256_RE = re.compile(r"[0-9A-F]{64}")
_OPEN_DATASET_TEST_CALLER = (
    "scripts/test_emotion_state_001_open_dataset_gate.py"
)
_CLOSEOUT_TEST_CALLER = (
    "scripts/test_emotion_state_001_closeout_hardening.py"
)
_REVIEWED_INLINE_CALLER_DIGESTS = {
    _OPEN_DATASET_TEST_CALLER: frozenset({
        "67BE07A2010F3F5F7857E274F59A523196A8B2071270043F5A30D0C80E849662",
        "D0E83A77224E603F97B3DE9B25983BB4AA27C3116BE66FE11B922813AAADE8AA",
        "B2D78EC951F391DD6167342124D80968AD88C9D72C7F7F1B082D273AFA531886",
        "0C84AD0AB699783710EE7729306E5D8763C8013297A26BE3197EA68AE3500A67",
    }),
    _CLOSEOUT_TEST_CALLER: frozenset({
        "6A2DA06455D5DAD127FF5C6446BE3CCB247A7258BFD2E5ECC12D363E70C72473",
    }),
}

_ORIGINAL_BUILTINS_OPEN = builtins.open
_ORIGINAL_IO_OPEN = io.open
_ORIGINAL_OS_OPEN = os.open
_ORIGINAL_OS_STAT = os.stat
_ORIGINAL_OS_LSTAT = os.lstat
_ORIGINAL_OS_LISTDIR = os.listdir
_ORIGINAL_OS_SCANDIR = os.scandir
_ORIGINAL_OS_READLINK = os.readlink
_ORIGINAL_OS_EXIT = os._exit
_ORIGINAL_POPEN = subprocess.Popen
_ORIGINAL_SOCKET = socket.socket
_SITE_PATH = os.path.realpath(os.path.abspath(__file__))
_GUARD_SITE_DIR = os.path.dirname(_SITE_PATH)
_RESOLUTION_STATE = threading.local()
_RULE_USE_LOCK = threading.Lock()
_TRANSACTION_ENVIRONMENT_NAMES = ("HOME", "USERPROFILE", "TEMP", "TMP")
_FIXED_GUARD_CONTROL_NAMES = (
    "EMOTION_STATE_PHASE_A_GUARD_POLICY",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_TERMINAL_PROMPT",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONIOENCODING",
    "PYTHONPATH",
    "PYTHONUTF8",
)
_STARTUP_ANCHORS: Mapping[str, str] = MappingProxyType({})


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(raw_value: str, *, label: str) -> object:
    if not isinstance(raw_value, str):
        raise ValueError(f"{label} must be text")
    try:
        return json.loads(
            raw_value,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"invalid JSON constant: {value}")
            ),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is invalid JSON") from exc


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _normalized_path(path: object) -> str:
    raw_path = os.fspath(path)
    if isinstance(raw_path, bytes):
        return os.fsdecode(raw_path)
    if not isinstance(raw_path, str):
        raise TypeError("path must resolve to text or bytes")
    return raw_path


def _comparison_path(path: str) -> str:
    normalized = os.path.normpath(path)
    return os.path.normcase(normalized) if os.name == "nt" else normalized


def _is_within(path: str, root: str, *, strict: bool = False) -> bool:
    comparable_path = _comparison_path(path)
    comparable_root = _comparison_path(root)
    try:
        common = os.path.commonpath((comparable_path, comparable_root))
    except ValueError:
        return False
    if common != comparable_root:
        return False
    return not strict or comparable_path != comparable_root


def _normalize_rule_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"{label} must be a non-empty string")
    normalized = value.replace("\\", "/")
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise ValueError(f"{label} must be a contained relative POSIX path")
    return normalized


def _validate_string_array(value: object, *, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or "\x00" in item:
            raise ValueError(f"{label} must contain only strings")
        result.append(item)
    return result


def _semantic_rule_key(rule: Mapping[str, object]) -> tuple[object, ...]:
    kind = rule["kind"]
    if kind == "python_inline":
        return (
            kind,
            rule["caller"],
            rule["source_sha256"],
            rule["cwd_class"],
            rule["environment_class"],
        )
    if kind == "python_target":
        return (
            kind,
            rule["caller"],
            rule["target"],
            tuple(rule["args"]),
            rule["cwd_class"],
            rule["environment_class"],
        )
    return (
        kind,
        rule["caller"],
        rule["matcher_id"],
        rule["cwd_class"],
        rule.get("captured_head"),
        rule.get("sentinel_object_id"),
    )


def _validate_rule_array(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("allowed subprocess rules must be a JSON array")
    normalized_rules: list[dict[str, object]] = []
    semantic_keys: set[tuple[object, ...]] = set()
    for supplied_rule in value:
        if not isinstance(supplied_rule, dict):
            raise ValueError("allowed subprocess rule must be an object")
        kind = supplied_rule.get("kind")
        if kind not in _RULE_KINDS:
            raise ValueError("allowed subprocess rule kind is not closed")
        if kind == "python_inline":
            expected_keys = {
                "kind",
                "caller",
                "source_sha256",
                "cwd_class",
                "environment_class",
                "max_uses",
                "children",
            }
        elif kind == "python_target":
            expected_keys = {
                "kind",
                "caller",
                "target",
                "args",
                "cwd_class",
                "environment_class",
                "max_uses",
                "children",
            }
        else:
            matcher_id = supplied_rule.get("matcher_id")
            if matcher_id not in _GIT_MATCHER_IDS:
                raise ValueError("Git matcher ID is not closed")
            expected_keys = {
                "kind",
                "caller",
                "matcher_id",
                "cwd_class",
                "children",
            }
            if matcher_id == "project_root_sentinel":
                expected_keys.update({
                    "captured_head",
                    "sentinel_object_id",
                })
        if set(supplied_rule) != expected_keys:
            raise ValueError("allowed subprocess rule fields are not closed")

        rule = dict(supplied_rule)
        rule["caller"] = _normalize_rule_path(
            rule["caller"],
            label="rule caller",
        )
        if rule["cwd_class"] not in _CWD_CLASSES:
            raise ValueError("rule cwd_class is not closed")
        if kind in {"python_inline", "python_target"}:
            if rule["environment_class"] not in _ENVIRONMENT_CLASSES:
                raise ValueError("rule environment_class is not closed")
            if (
                type(rule["max_uses"]) is not int
                or rule["max_uses"] < 1
            ):
                raise ValueError("rule max_uses must be a positive integer")
        if kind == "python_inline":
            if (
                not isinstance(rule["source_sha256"], str)
                or _UPPER_SHA256_RE.fullmatch(rule["source_sha256"]) is None
            ):
                raise ValueError("inline source digest must be uppercase SHA-256")
            reviewed_digests = _REVIEWED_INLINE_CALLER_DIGESTS.get(
                rule["caller"]
            )
            if (
                reviewed_digests is None
                or rule["source_sha256"] not in reviewed_digests
            ):
                raise ValueError("inline caller and source digest are not reviewed")
            if rule["environment_class"] == "synthetic_guard" and (
                rule["caller"] != _OPEN_DATASET_TEST_CALLER
                or rule["cwd_class"] != "transaction_descendant"
            ):
                raise ValueError("synthetic inline rule differs from reviewed scope")
            if rule["caller"] == _CLOSEOUT_TEST_CALLER and (
                rule["cwd_class"] != "project_root"
                or rule["environment_class"] != "inherit"
            ):
                raise ValueError("closeout inline rule differs from reviewed scope")
        elif kind == "python_target":
            rule["target"] = _normalize_rule_path(
                rule["target"],
                label="rule target",
            )
            rule["args"] = _validate_string_array(
                rule["args"],
                label="rule args",
            )
        elif rule["matcher_id"] == "project_root_sentinel":
            if (
                not isinstance(rule["captured_head"], str)
                or _LOWER_HEX_40_RE.fullmatch(rule["captured_head"]) is None
            ):
                raise ValueError("captured_head must be lowercase 40-hex")
            if (
                not isinstance(rule["sentinel_object_id"], str)
                or _LOWER_HEX_OBJECT_RE.fullmatch(
                    rule["sentinel_object_id"]
                )
                is None
            ):
                raise ValueError(
                    "sentinel_object_id must be lowercase 40-or-64-hex"
                )
        rule["children"] = _validate_rule_array(rule["children"])
        semantic_key = _semantic_rule_key(rule)
        if semantic_key in semantic_keys:
            raise ValueError("duplicate or ambiguous subprocess rule")
        semantic_keys.add(semantic_key)
        normalized_rules.append(rule)
    return normalized_rules


def _credential_name(name: str) -> bool:
    uppercase_name = name.upper()
    return (
        uppercase_name in _PROVIDER_EXACT_NAMES
        or any(
            uppercase_name.startswith(prefix)
            for prefix in _PROVIDER_PREFIXES
        )
        or _CREDENTIAL_NAME_RE.search(uppercase_name) is not None
    )


def _validate_environment(environment: object) -> dict[str, str]:
    if not isinstance(environment, Mapping):
        raise PermissionError(_PROCESS_DENIAL)
    normalized: dict[str, str] = {}
    for name, value in environment.items():
        if (
            not isinstance(name, str)
            or not name
            or "\x00" in name
            or not isinstance(value, str)
        ):
            raise PermissionError(_PROCESS_DENIAL)
        uppercase_name = name.upper()
        if uppercase_name in normalized:
            raise PermissionError(_PROCESS_DENIAL)
        normalized[uppercase_name] = value
    return normalized


def _same_path(first: str, second: str) -> bool:
    return _comparison_path(os.path.abspath(first)) == _comparison_path(
        os.path.abspath(second)
    )


def _validated_transaction_root(
    environment: Mapping[str, str],
    project_root: str,
) -> str:
    supplied_values = [
        environment.get(name) for name in _TRANSACTION_ENVIRONMENT_NAMES
    ]
    if any(not value for value in supplied_values):
        raise PermissionError(_PROCESS_DENIAL)
    lexical_paths = [
        os.path.abspath(value)
        for value in supplied_values
        if value is not None
    ]
    lexical = lexical_paths[0]
    if any(not _same_path(lexical, path) for path in lexical_paths[1:]):
        raise PermissionError(_PROCESS_DENIAL)
    resolved = os.path.realpath(lexical)
    if (
        not os.path.isdir(resolved)
        or not _is_within(lexical, project_root, strict=True)
        or not _is_within(resolved, project_root, strict=True)
    ):
        raise PermissionError(_PROCESS_DENIAL)
    return resolved


def _require_anchored_controls(
    supplied: Mapping[str, str],
    *,
    include_project_root: bool,
) -> None:
    names = list(_FIXED_GUARD_CONTROL_NAMES)
    if include_project_root:
        names.append("EMOTION_STATE_PHASE_A_PROJECT_ROOT")
    for name in names:
        if supplied.get(name) != _STARTUP_ANCHORS.get(name):
            raise PermissionError(_PROCESS_DENIAL)


def _clean_parent_environment(
    supplied: Mapping[str, str],
) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for name, value in supplied.items():
        if name in _PARENT_ALLOWLIST and not _credential_name(name):
            cleaned[name] = value
    return cleaned


def _scrub_child_environment(
    environment: object,
    *,
    children: list[dict[str, object]],
    environment_class: str,
    child_cwd: str,
) -> dict[str, str]:
    supplied = _validate_environment(environment)
    cleaned = _clean_parent_environment(supplied)
    if environment_class == "synthetic_guard":
        if any(_credential_name(name) for name in supplied):
            raise PermissionError(_PROCESS_DENIAL)
        child_root_value = supplied.get(
            "EMOTION_STATE_PHASE_A_PROJECT_ROOT"
        )
        if not child_root_value:
            raise PermissionError(_PROCESS_DENIAL)
        child_root = os.path.realpath(os.path.abspath(child_root_value))
        if not _same_path(child_root, child_cwd):
            raise PermissionError(_PROCESS_DENIAL)
        _require_anchored_controls(
            supplied,
            include_project_root=False,
        )
        _validated_transaction_root(supplied, child_root)
        for name in _FIXED_GUARD_CONTROL_NAMES:
            cleaned[name] = _STARTUP_ANCHORS[name]
        cleaned["EMOTION_STATE_PHASE_A_PROJECT_ROOT"] = child_root_value
        for name in _TRANSACTION_ENVIRONMENT_NAMES:
            cleaned[name] = supplied[name]
    elif environment_class == "guarded_child":
        _require_anchored_controls(
            supplied,
            include_project_root=True,
        )
        child_transaction_root = _validated_transaction_root(
            supplied,
            _PROJECT_ROOT,
        )
        if _same_path(child_transaction_root, _TRANSACTION_ROOT):
            raise PermissionError(_PROCESS_DENIAL)
        for name in (
            *_FIXED_GUARD_CONTROL_NAMES,
            "EMOTION_STATE_PHASE_A_PROJECT_ROOT",
        ):
            cleaned[name] = _STARTUP_ANCHORS[name]
        for name in _TRANSACTION_ENVIRONMENT_NAMES:
            cleaned[name] = supplied[name]
    else:
        for name, value in _STARTUP_ANCHORS.items():
            cleaned[name] = value
    cleaned["EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON"] = (
        _canonical_json(children)
    )
    return cleaned


def _caller_identity() -> str | None:
    frame = inspect.currentframe()
    try:
        if frame is not None:
            frame = frame.f_back
        while frame is not None:
            filename = frame.f_code.co_filename
            frame = frame.f_back
            if not filename or filename.startswith("<"):
                continue
            candidate = os.path.realpath(os.path.abspath(filename))
            if _same_path(candidate, _SITE_PATH):
                continue
            if not _is_within(candidate, _PROJECT_ROOT, strict=True):
                continue
            relative = os.path.relpath(candidate, _PROJECT_ROOT)
            return relative.replace("\\", "/")
    finally:
        del frame
    return None


def _resolved_cwd(cwd: object) -> tuple[str, str]:
    if cwd is None:
        lexical = os.path.abspath(os.getcwd())
    else:
        try:
            lexical = os.path.abspath(_normalized_path(cwd))
        except (TypeError, ValueError, OSError) as exc:
            raise PermissionError(_PROCESS_DENIAL) from exc
    resolved = os.path.realpath(lexical)
    if not os.path.isdir(resolved):
        raise PermissionError(_PROCESS_DENIAL)
    return lexical, resolved


def _cwd_matches(cwd_class: str, lexical: str, resolved: str) -> bool:
    if cwd_class == "project_root":
        return _same_path(lexical, _PROJECT_ROOT) and _same_path(
            resolved,
            _PROJECT_ROOT,
        )
    return (
        _is_within(lexical, _TRANSACTION_ROOT, strict=True)
        and _is_within(resolved, _TRANSACTION_ROOT, strict=True)
    )


def _command_items(command: object) -> list[str]:
    if isinstance(command, (str, bytes)) or not isinstance(command, Sequence):
        raise PermissionError(_PROCESS_DENIAL)
    items: list[str] = []
    for item in command:
        try:
            normalized = _normalized_path(item)
        except (TypeError, ValueError, OSError) as exc:
            raise PermissionError(_PROCESS_DENIAL) from exc
        if "\x00" in normalized:
            raise PermissionError(_PROCESS_DENIAL)
        items.append(normalized)
    if not items:
        raise PermissionError(_PROCESS_DENIAL)
    return items


def _is_current_python(value: str) -> bool:
    if not os.path.isabs(value):
        return False
    return _same_path(value, sys.executable)


def _resolved_python_target(
    value: str,
    *,
    cwd: str,
    expected_relative_path: str,
) -> bool:
    if "\x00" in value:
        return False
    if os.path.isabs(value):
        lexical = os.path.abspath(value)
    else:
        normalized = value.replace("\\", "/")
        if (
            normalized.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized)
            or ".." in normalized.split("/")
        ):
            return False
        lexical = os.path.abspath(os.path.join(cwd, value))
    expected = os.path.abspath(
        os.path.join(_PROJECT_ROOT, *expected_relative_path.split("/"))
    )
    resolved = os.path.realpath(lexical)
    expected_resolved = os.path.realpath(expected)
    return (
        _is_within(lexical, _PROJECT_ROOT, strict=True)
        and _is_within(resolved, _PROJECT_ROOT, strict=True)
        and _same_path(resolved, expected_resolved)
        and _same_path(expected, expected_resolved)
    )


def _contained_git_path(value: str) -> bool:
    if (
        not value
        or "\x00" in value
        or value.startswith(("/", "\\", ":("))
        or re.match(r"^[A-Za-z]:", value)
    ):
        return False
    normalized = value.replace("\\", "/")
    return all(part not in {"", ".", ".."} for part in normalized.split("/"))


def _literal_fixture_git_add_path(value: str) -> bool:
    return (
        _contained_git_path(value)
        and not value.startswith(":")
        and not any(character in value for character in "*?[")
    )


def _literal_git_path(value: str) -> bool:
    prefix = ":(literal)"
    return value.startswith(prefix) and _contained_git_path(value[len(prefix) :])


def _path_is_link_or_reparse(path: str) -> bool:
    status = _ORIGINAL_OS_LSTAT(path)
    reparse_attribute = getattr(
        stat,
        "FILE_ATTRIBUTE_REPARSE_POINT",
        0x400,
    )
    return stat.S_ISLNK(status.st_mode) or bool(
        getattr(status, "st_file_attributes", 0) & reparse_attribute
    )


def _existing_path_chain_is_safe(root: str, candidate: str) -> bool:
    root_path = os.path.abspath(root)
    candidate_path = os.path.abspath(candidate)
    if not _is_within(candidate_path, root_path):
        return False
    try:
        relative = os.path.relpath(candidate_path, root_path)
    except ValueError:
        return False
    current = root_path
    paths = [current]
    if relative != ".":
        for part in relative.split(os.sep):
            current = os.path.join(current, part)
            paths.append(current)
    for path in paths:
        try:
            if _path_is_link_or_reparse(path):
                return False
        except FileNotFoundError:
            break
        except OSError:
            return False
        resolved = os.path.realpath(path)
        if (
            not _same_path(path, resolved)
            or not _is_within(resolved, root_path)
        ):
            return False
    return True


def _fixture_git_operands(argv: list[str]) -> list[str]:
    if len(argv) >= 4 and argv[:3] == ["git", "add", "--"]:
        return argv[3:]
    if len(argv) >= 5 and argv[:4] == ["git", "add", "-f", "--"]:
        return argv[4:]
    if argv == [
        "git",
        "mv",
        "--",
        "renamed-old.py",
        "renamed-new.py",
    ]:
        return argv[3:]
    return []


def _fixture_git_add_operands(argv: list[str]) -> list[str] | None:
    if len(argv) >= 4 and argv[:3] == ["git", "add", "--"]:
        return argv[3:]
    if len(argv) >= 5 and argv[:4] == ["git", "add", "-f", "--"]:
        return argv[4:]
    return None


def _fixture_git_add_operand_is_safe(
    operand: str,
    *,
    cwd: str,
) -> bool:
    if not _literal_fixture_git_add_path(operand):
        return False
    candidate = os.path.join(cwd, *operand.replace("\\", "/").split("/"))
    parent = os.path.dirname(candidate)
    if not _existing_path_chain_is_safe(_TRANSACTION_ROOT, parent):
        return False
    try:
        parent_status = _ORIGINAL_OS_LSTAT(parent)
    except OSError:
        return False
    if (
        not stat.S_ISDIR(parent_status.st_mode)
        or _path_is_link_or_reparse(parent)
    ):
        return False
    try:
        candidate_status = _ORIGINAL_OS_LSTAT(candidate)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return (
        stat.S_ISREG(candidate_status.st_mode)
        and not _path_is_link_or_reparse(candidate)
        and _existing_path_chain_is_safe(
            _TRANSACTION_ROOT,
            candidate,
        )
    )


def _fixture_git_paths_are_safe(
    argv: list[str],
    *,
    cwd: str,
) -> bool:
    if not _existing_path_chain_is_safe(_TRANSACTION_ROOT, cwd):
        return False
    add_operands = _fixture_git_add_operands(argv)
    if add_operands is not None:
        return all(
            _fixture_git_add_operand_is_safe(operand, cwd=cwd)
            for operand in add_operands
        )
    for operand in _fixture_git_operands(argv):
        candidate = os.path.join(cwd, *operand.replace("\\", "/").split("/"))
        if not _existing_path_chain_is_safe(_TRANSACTION_ROOT, candidate):
            return False
    return True


def _fixture_git_match(argv: list[str]) -> bool:
    if argv in (
        ["git", "init"],
        ["git", "config", "user.email", "fixture@example.invalid"],
        ["git", "config", "user.name", "Fixture Author"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "config", "core.filemode", "false"],
        ["git", "rev-parse", "HEAD"],
        ["git", "mv", "--", "renamed-old.py", "renamed-new.py"],
    ):
        return True
    if (
        len(argv) == 4
        and argv[:3] == ["git", "commit", "-m"]
        and argv[3] in _FIXTURE_COMMIT_MESSAGES
    ):
        return True
    if len(argv) >= 4 and argv[:3] == ["git", "add", "--"]:
        return all(
            _literal_fixture_git_add_path(path) for path in argv[3:]
        )
    if len(argv) >= 5 and argv[:4] == ["git", "add", "-f", "--"]:
        return all(
            _literal_fixture_git_add_path(path) for path in argv[4:]
        )
    return (
        len(argv) == 5
        and argv[:4] == [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
        ]
        and re.fullmatch(r"[0-9a-f]{40}\.\.[0-9a-f]{40}", argv[4])
        is not None
    )


def _transaction_verification_git_match(argv: list[str]) -> bool:
    prefix = ["git", "--no-lazy-fetch"]
    if argv[:2] != prefix or argv.count("--no-lazy-fetch") != 1:
        return False
    command = argv[2:]
    if command == ["rev-parse", "--verify", "HEAD^{commit}"]:
        return True
    if (
        len(command) == 3
        and command[:2] == ["rev-parse", "--verify"]
        and re.fullmatch(r"[0-9a-f]{40}\^\{commit\}", command[2])
        is not None
    ):
        return True
    if (
        len(command) == 6
        and command[:2] == ["ls-tree", "-z"]
        and _LOWER_HEX_40_RE.fullmatch(command[2]) is not None
        and command[3] == "--"
        and _literal_git_path(command[4])
    ):
        return False
    if (
        len(command) == 5
        and command[:2] == ["ls-tree", "-z"]
        and _LOWER_HEX_40_RE.fullmatch(command[2]) is not None
        and command[3] == "--"
        and _literal_git_path(command[4])
    ):
        return True
    if (
        len(command) == 6
        and command[:3] == ["ls-files", "--stage", "-z"]
        and command[3] == "--"
        and _literal_git_path(command[4])
    ):
        return False
    if (
        len(command) == 5
        and command[:3] == ["ls-files", "--stage", "-z"]
        and command[3] == "--"
        and _literal_git_path(command[4])
    ):
        return True
    if (
        len(command) == 3
        and command[:2] == ["cat-file", "blob"]
        and _LOWER_HEX_OBJECT_RE.fullmatch(command[2]) is not None
    ):
        return True
    if command == [
        "diff",
        "--cached",
        "--name-status",
        "-z",
        "--find-renames",
        "--",
    ]:
        return True
    if (
        len(command) == 7
        and command[:5] == [
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--find-renames",
        ]
        and _LOWER_HEX_40_RE.fullmatch(command[5]) is not None
        and command[6] == "--"
    ):
        return True
    if command == [
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        "--",
    ]:
        return True
    if (
        len(command) == 6
        and command[:4] == [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
        ]
        and re.fullmatch(r"[0-9a-f]{40}\.\.[0-9a-f]{40}", command[4])
        is not None
        and command[5] == "--"
    ):
        return True
    return command in (
        ["ls-files", "--others", "--exclude-standard", "-z", "--"],
        ["ls-files", "-z", "--", "runtime"],
    )


def _project_sentinel_git_match(
    argv: list[str],
    rule: Mapping[str, object],
) -> bool:
    return argv in (
        [
            "git",
            "--no-lazy-fetch",
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ],
        [
            "git",
            "--no-lazy-fetch",
            "ls-tree",
            "-z",
            rule["captured_head"],
            "--",
            ":(literal)data/private/.gitignore",
        ],
        [
            "git",
            "--no-lazy-fetch",
            "cat-file",
            "blob",
            rule["sentinel_object_id"],
        ],
    )


def _git_rule_execution(
    argv: list[str],
    rule: Mapping[str, object],
) -> list[str] | None:
    matcher_id = rule["matcher_id"]
    if matcher_id == "transaction_fixture":
        return argv if _fixture_git_match(argv) else None
    if matcher_id == "transaction_verification":
        return argv if _transaction_verification_git_match(argv) else None
    if matcher_id == "project_root_sentinel":
        return argv if _project_sentinel_git_match(argv, rule) else None
    canonical = ["git", "status", "--short", "--untracked-files=all"]
    if argv != canonical:
        return None
    return [
        "git",
        "--no-lazy-fetch",
        "status",
        "--short",
        "--untracked-files=all",
    ]


def _rule_execution(
    rule: Mapping[str, object],
    *,
    caller: str,
    argv: list[str],
    cwd_lexical: str,
    cwd_resolved: str,
) -> tuple[list[str], str] | None:
    if rule["caller"] != caller or not _cwd_matches(
        rule["cwd_class"],
        cwd_lexical,
        cwd_resolved,
    ):
        return None
    if rule["kind"] == "python_inline":
        if (
            len(argv) != 3
            or not _is_current_python(argv[0])
            or argv[1] != "-c"
        ):
            return None
        digest = hashlib.sha256(argv[2].encode("utf-8")).hexdigest().upper()
        if digest != rule["source_sha256"]:
            return None
        return argv, rule["environment_class"]
    if rule["kind"] == "python_target":
        if len(argv) < 2 or not _is_current_python(argv[0]):
            return None
        if not _resolved_python_target(
            argv[1],
            cwd=cwd_resolved,
            expected_relative_path=rule["target"],
        ):
            return None
        if argv[2:] != rule["args"]:
            return None
        return argv, rule["environment_class"]
    if argv[0] != "git":
        return None
    if (
        rule["matcher_id"] == "transaction_fixture"
        and not _fixture_git_paths_are_safe(argv, cwd=cwd_lexical)
    ):
        return None
    execution_argv = _git_rule_execution(argv, rule)
    if execution_argv is None:
        return None
    return execution_argv, "inherit"


def _reject_inherited_descriptors(bound: inspect.BoundArguments) -> None:
    for name in ("stdin", "stdout", "stderr"):
        value = bound.arguments.get(name)
        if value is None:
            continue
        if type(value) is int and value in {-3, -2, -1, 0, 1, 2}:
            continue
        raise PermissionError(_PROCESS_DENIAL)
    startupinfo = bound.arguments.get("startupinfo")
    attribute_list = getattr(startupinfo, "lpAttributeList", None)
    if isinstance(attribute_list, Mapping) and attribute_list.get("handle_list"):
        raise PermissionError(_PROCESS_DENIAL)


def _guarded_popen_arguments(
    *popen_args: object,
    **popen_kwargs: object,
) -> inspect.BoundArguments:
    try:
        bound = inspect.signature(_ORIGINAL_POPEN).bind_partial(
            *popen_args,
            **popen_kwargs,
        )
    except TypeError as exc:
        raise PermissionError(_PROCESS_DENIAL) from exc
    command = _command_items(bound.arguments.get("args"))
    if bound.arguments.get("shell", False) is not False:
        raise PermissionError(_PROCESS_DENIAL)
    if bound.arguments.get("executable") is not None:
        raise PermissionError(_PROCESS_DENIAL)
    if bound.arguments.get("preexec_fn") is not None:
        raise PermissionError(_PROCESS_DENIAL)
    pass_fds = bound.arguments.get("pass_fds", ())
    if pass_fds:
        raise PermissionError(_PROCESS_DENIAL)
    _reject_inherited_descriptors(bound)

    cwd_lexical, cwd_resolved = _resolved_cwd(bound.arguments.get("cwd"))
    caller = _caller_identity()
    if caller is None:
        raise PermissionError(_PROCESS_DENIAL)
    matches: list[tuple[int, list[str], str]] = []
    for index, rule in enumerate(_RULES):
        matched = _rule_execution(
            rule,
            caller=caller,
            argv=command,
            cwd_lexical=cwd_lexical,
            cwd_resolved=cwd_resolved,
        )
        if matched is not None:
            matches.append((index, matched[0], matched[1]))
    if len(matches) != 1:
        raise PermissionError(_PROCESS_DENIAL)
    rule_index, execution_argv, environment_class = matches[0]
    rule = _RULES[rule_index]
    if rule["kind"] in {"python_inline", "python_target"}:
        with _RULE_USE_LOCK:
            if _RULE_USE_COUNTS[rule_index] >= rule["max_uses"]:
                raise PermissionError(_PROCESS_DENIAL)
            _RULE_USE_COUNTS[rule_index] += 1

    supplied_environment = bound.arguments.get("env")
    if supplied_environment is None:
        supplied_environment = os.environ
    child_environment = _scrub_child_environment(
        supplied_environment,
        children=rule["children"],
        environment_class=environment_class,
        child_cwd=cwd_resolved,
    )
    bound.arguments["args"] = execution_argv
    bound.arguments["env"] = child_environment
    bound.arguments["shell"] = False
    bound.arguments["close_fds"] = True
    return bound


class _GuardedPopen(_ORIGINAL_POPEN):
    def __init__(self, *popen_args: object, **popen_kwargs: object) -> None:
        bound = _guarded_popen_arguments(*popen_args, **popen_kwargs)
        _ORIGINAL_POPEN.__init__(self, *bound.args, **bound.kwargs)


def _deny_process(*_args: object, **_kwargs: object) -> None:
    raise PermissionError(_PROCESS_DENIAL)


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise PermissionError(_NETWORK_DENIAL)


class _GuardedSocket(_ORIGINAL_SOCKET):
    def __new__(
        cls,
        family: int = socket.AF_INET,
        type: int = socket.SOCK_STREAM,
        proto: int = 0,
        fileno: int | None = None,
    ):
        if family in {socket.AF_INET, socket.AF_INET6}:
            _deny_network()
        return super().__new__(cls)

    connect = _deny_network
    connect_ex = _deny_network
    send = _deny_network
    sendall = _deny_network
    sendto = _deny_network
    bind = _deny_network
    listen = _deny_network
    accept = _deny_network
    recv = _deny_network
    recv_into = _deny_network
    recvfrom = _deny_network
    recvfrom_into = _deny_network
    shutdown = _deny_network
    if hasattr(_ORIGINAL_SOCKET, "sendmsg"):
        sendmsg = _deny_network
    if hasattr(_ORIGINAL_SOCKET, "recvmsg"):
        recvmsg = _deny_network
    if hasattr(_ORIGINAL_SOCKET, "recvmsg_into"):
        recvmsg_into = _deny_network


def _path_is_private(path: str) -> bool:
    return any(_is_within(path, private_root) for private_root in _PRIVATE_ROOTS)


def _check_path(path: object, *, dir_fd: object = None) -> None:
    if dir_fd is not None:
        raise PermissionError(_PRIVATE_DENIAL)
    if isinstance(path, int):
        return
    try:
        raw_path = _normalized_path(path)
    except (TypeError, ValueError, OSError):
        return
    lexical = os.path.abspath(raw_path)
    if _path_is_private(lexical):
        raise PermissionError(_PRIVATE_DENIAL)
    if getattr(_RESOLUTION_STATE, "active", False):
        return
    _RESOLUTION_STATE.active = True
    try:
        resolved = os.path.realpath(lexical)
    finally:
        _RESOLUTION_STATE.active = False
    if _path_is_private(resolved):
        raise PermissionError(_PRIVATE_DENIAL)


def _guarded_builtin_open(file: object, *args: object, **kwargs: object):
    _check_path(file)
    return _ORIGINAL_BUILTINS_OPEN(file, *args, **kwargs)


def _guarded_io_open(file: object, *args: object, **kwargs: object):
    _check_path(file)
    return _ORIGINAL_IO_OPEN(file, *args, **kwargs)


def _guarded_os_open(
    path: object,
    flags: int,
    mode: int = 0o777,
    *,
    dir_fd: int | None = None,
):
    _check_path(path, dir_fd=dir_fd)
    return _ORIGINAL_OS_OPEN(path, flags, mode, dir_fd=dir_fd)


def _guarded_os_stat(
    path: object,
    *,
    dir_fd: int | None = None,
    follow_symlinks: bool = True,
):
    if getattr(_RESOLUTION_STATE, "active", False):
        return _ORIGINAL_OS_STAT(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )
    _check_path(path, dir_fd=dir_fd)
    return _ORIGINAL_OS_STAT(
        path,
        dir_fd=dir_fd,
        follow_symlinks=follow_symlinks,
    )


def _guarded_os_lstat(path: object, *, dir_fd: int | None = None):
    if getattr(_RESOLUTION_STATE, "active", False):
        return _ORIGINAL_OS_LSTAT(path, dir_fd=dir_fd)
    _check_path(path, dir_fd=dir_fd)
    return _ORIGINAL_OS_LSTAT(path, dir_fd=dir_fd)


def _guarded_os_listdir(path: object = "."):
    if getattr(_RESOLUTION_STATE, "active", False):
        return _ORIGINAL_OS_LISTDIR(path)
    _check_path(path)
    return _ORIGINAL_OS_LISTDIR(path)


def _guarded_os_scandir(path: object = "."):
    if getattr(_RESOLUTION_STATE, "active", False):
        return _ORIGINAL_OS_SCANDIR(path)
    _check_path(path)
    return _ORIGINAL_OS_SCANDIR(path)


def _guarded_os_readlink(path: object, *, dir_fd: int | None = None):
    if getattr(_RESOLUTION_STATE, "active", False):
        return _ORIGINAL_OS_READLINK(path, dir_fd=dir_fd)
    _check_path(path, dir_fd=dir_fd)
    return _ORIGINAL_OS_READLINK(path, dir_fd=dir_fd)


def _install_filesystem_guard() -> None:
    builtins.open = _guarded_builtin_open
    io.open = _guarded_io_open
    os.open = _guarded_os_open
    os.stat = _guarded_os_stat
    os.lstat = _guarded_os_lstat
    os.listdir = _guarded_os_listdir
    os.scandir = _guarded_os_scandir
    os.readlink = _guarded_os_readlink


def _install_network_guard() -> None:
    socket.socket = _GuardedSocket
    socket.SocketType = _GuardedSocket
    for name in (
        "create_connection",
        "create_server",
        "socketpair",
        "fromfd",
        "fromshare",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
    ):
        if hasattr(socket, name):
            setattr(socket, name, _deny_network)


def _install_process_guard() -> None:
    subprocess.Popen = _GuardedPopen
    for name in ("system", "popen", "startfile"):
        if hasattr(os, name):
            setattr(os, name, _deny_process)
    for name in dir(os):
        if name.startswith(("spawn", "exec")) and callable(getattr(os, name)):
            setattr(os, name, _deny_process)


def _activate() -> None:
    global _POLICY_PATH
    global _PROJECT_ROOT
    global _TRANSACTION_ROOT
    global _PRIVATE_ROOTS
    global _PARENT_ALLOWLIST
    global _GUARD_GENERATED_NAMES
    global _PROVIDER_EXACT_NAMES
    global _PROVIDER_PREFIXES
    global _CREDENTIAL_NAME_RE
    global _RULES
    global _RULE_USE_COUNTS
    global _STARTUP_ANCHORS

    policy_value = os.environ.get("EMOTION_STATE_PHASE_A_GUARD_POLICY")
    if policy_value is None:
        return
    _POLICY_PATH = os.path.realpath(os.path.abspath(policy_value))
    with _ORIGINAL_BUILTINS_OPEN(_POLICY_PATH, "rb") as policy_handle:
        policy_bytes = policy_handle.read()
    if hashlib.sha256(policy_bytes).hexdigest().upper() != _POLICY_DIGEST:
        raise ValueError("guard policy bytes differ")
    policy = json.loads(
        policy_bytes.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_json_keys,
    )
    if (
        not isinstance(policy, dict)
        or policy.get("policy_id") != _POLICY_ID
        or policy.get("schema_version") != 1
        or policy.get("network_allowed") is not False
        or policy.get("private_path_prefixes")
        != ["data/private", "data/private-restricted"]
    ):
        raise ValueError("guard policy semantics differ")

    project_value = os.environ.get("EMOTION_STATE_PHASE_A_PROJECT_ROOT")
    if not project_value:
        raise ValueError("guard project root is missing")
    _PROJECT_ROOT = os.path.realpath(os.path.abspath(project_value))
    if not os.path.isdir(_PROJECT_ROOT):
        raise ValueError("guard project root is unavailable")
    startup_environment = _validate_environment(os.environ)
    _TRANSACTION_ROOT = _validated_transaction_root(
        startup_environment,
        _PROJECT_ROOT,
    )
    _PRIVATE_ROOTS = tuple(
        os.path.abspath(
            os.path.join(_PROJECT_ROOT, *prefix.split("/"))
        )
        for prefix in policy["private_path_prefixes"]
    )
    _PARENT_ALLOWLIST = {
        name.upper() for name in policy["parent_environment_allowlist"]
    }
    _GUARD_GENERATED_NAMES = {
        name.upper() for name in policy["guard_generated_environment_names"]
    }
    _PROVIDER_EXACT_NAMES = {
        name.upper() for name in policy["provider_environment_exact_names"]
    }
    _PROVIDER_PREFIXES = tuple(
        prefix.upper() for prefix in policy["provider_environment_prefixes"]
    )
    _CREDENTIAL_NAME_RE = re.compile(
        policy["credential_environment_name_pattern"],
        re.IGNORECASE,
    )
    raw_rules = os.environ.get(
        "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON"
    )
    if raw_rules is None:
        raise ValueError("allowed subprocess rules are missing")
    _RULES = _validate_rule_array(
        _load_json(raw_rules, label="allowed subprocess rules")
    )
    anchor_names = (
        *_FIXED_GUARD_CONTROL_NAMES,
        "EMOTION_STATE_PHASE_A_PROJECT_ROOT",
        *_TRANSACTION_ENVIRONMENT_NAMES,
    )
    anchors: dict[str, str] = {}
    for name in anchor_names:
        value = startup_environment.get(name)
        if value is None:
            raise ValueError(f"guard startup control is missing: {name}")
        anchors[name] = value
    _STARTUP_ANCHORS = MappingProxyType(anchors)
    _RULE_USE_COUNTS = [0 for _rule in _RULES]
    _install_filesystem_guard()
    _install_network_guard()
    _install_process_guard()


if os.environ.get("EMOTION_STATE_PHASE_A_GUARD_POLICY") is not None:
    try:
        _activate()
    except BaseException:
        try:
            sys.stderr.write(
                "EMOTION-STATE Phase A guard initialization failed\n"
            )
            sys.stderr.flush()
        finally:
            _ORIGINAL_OS_EXIT(86)
