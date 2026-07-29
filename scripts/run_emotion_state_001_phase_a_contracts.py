#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, Iterator

if os.name == "nt":
    import msvcrt
else:
    import fcntl


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.emotion_state_phase_a_contracts import (
    EXPECTED_IMPLEMENTATION_BASELINE_COMMIT,
    SELECTED_PUBLIC_DATASET_IDS,
    build_phase_a_payload,
    render_phase_a_report,
    validate_complete_payload,
    validate_material_pending_payload,
)
from scripts.emotion_state_phase_a_verification_evidence import (
    finalize_verification_evidence,
    persistent_verification_lock,
    prepare_verification_evidence,
    validate_active_verification_lock,
)


DEFAULT_CASE = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-001-phase-a-contracts.json"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "EMOTION-STATE-001-phase-a-contracts"
)
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
DEFAULT_RECOVERY_DIR = ROOT / ".tmp" / "emotion-state-001-phase-a-publication"
DEFAULT_MATERIAL_ROOT = ROOT / "data" / "public" / "emotion-state"
JOURNAL_NAME = "transaction.json"
LOCK_NAME = "publication.lock"
TRANSACTION_SCHEMA_VERSION = 2
IMPLEMENTATION_BASELINE_COMMIT = EXPECTED_IMPLEMENTATION_BASELINE_COMMIT
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
_TRANSACTION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_RECEIPT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")
MATERIAL_PENDING_DATASET_DIRECTORIES = {
    "crema-d-v1.0-audio-wav": "crema-d-v1.0",
    "ami-manual-annotations-v1.6.2": "ami-manual-annotations-v1.6.2",
}
_REPORT_COMMIT_MARKER_PATTERN = re.compile(
    r"(?m)^- Publication commit marker: `result\.json sha256:([0-9A-F]{64})`\r?$"
)


class EvidencePublicationError(RuntimeError):
    """A bounded, recoverable evidence-publication failure."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build EMOTION-STATE-001 Phase A contract evidence."
    )
    parser.add_argument("--case", default=str(DEFAULT_CASE))
    parser.add_argument("--out", default=str(DEFAULT_RESULT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--defer-acceptance", action="store_true")
    actions.add_argument("--accept-receipt")
    actions.add_argument("--reject-receipt")
    parser.add_argument("--mode", choices=("material-pending", "complete"))
    parser.add_argument("--receipt")
    parsed = parser.parse_args(argv)
    if parsed.defer_acceptance:
        if parsed.mode is None or parsed.receipt is None:
            parser.error("--defer-acceptance requires --mode and --receipt")
    elif parsed.mode is not None or parsed.receipt is not None:
        parser.error("--mode and --receipt are valid only with --defer-acceptance")
    return parsed


def _raw_path_parts(path_value: str) -> tuple[str, ...]:
    return tuple(
        part.casefold()
        for part in re.split(r"[\\/]+", path_value)
        if part not in ("", ".")
    )


def _contains_private_parts(parts: tuple[str, ...]) -> bool:
    return any(
        parts[index:index + len(private_parts)] == private_parts
        for private_parts in PRIVATE_PATH_PARTS
        for index in range(0, len(parts) - len(private_parts) + 1)
    )


def _contains_private_path(path: Path) -> bool:
    return _contains_private_parts(tuple(part.casefold() for part in path.parts))


def resolve_project_path(
    path_value: str,
    *,
    allowed_root: Path,
    inspect_lexical_chain: bool = False,
) -> Path:
    if not isinstance(path_value, str) or not path_value.strip() or "\x00" in path_value:
        raise ValueError("path must be a non-empty string")
    raw_parts = _raw_path_parts(path_value)
    if ".." in raw_parts:
        raise ValueError(f"parent traversal is blocked: {path_value}")
    if _contains_private_parts(raw_parts):
        raise ValueError(f"private path is blocked: {path_value}")
    try:
        candidate = Path(path_value)
        lexical_candidate = Path(os.path.abspath(
            candidate if candidate.is_absolute() else ROOT / candidate
        ))
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ValueError(f"path could not be resolved safely: {path_value}") from exc
    if inspect_lexical_chain:
        try:
            _validate_trusted_component_chain(
                lexical_candidate,
                trusted_root=ROOT,
            )
        except EvidencePublicationError as exc:
            raise ValueError(
                f"path component is a link or reparse point: {path_value}"
            ) from exc
    try:
        resolved = (
            candidate if candidate.is_absolute() else ROOT / candidate
        ).resolve(strict=False)
        project_root = ROOT.resolve(strict=False)
        resolved_allowed_root = Path(allowed_root).resolve(strict=False)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ValueError(f"path could not be resolved safely: {path_value}") from exc
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"path must stay inside project root: {path_value}") from exc
    if _contains_private_path(resolved):
        raise ValueError(f"private path is blocked: {path_value}")
    try:
        resolved.relative_to(resolved_allowed_root)
    except ValueError as exc:
        raise ValueError(f"path is outside its allowed artifact root: {path_value}") from exc
    return lexical_candidate


def validate_material_pending_dataset_absence(material_root: Path) -> None:
    """Fail closed when selected material exists under the bounded fixed or injected root."""

    try:
        root = Path(material_root)
    except TypeError as exc:
        raise ValueError("material-pending root must be path-like") from exc
    if root.exists():
        if not root.is_dir():
            raise ValueError("material-pending root must be a directory when present")
        if tuple(MATERIAL_PENDING_DATASET_DIRECTORIES) != SELECTED_PUBLIC_DATASET_IDS:
            raise ValueError("material-pending directory map does not match selected datasets")
        for dataset_id, directory_name in MATERIAL_PENDING_DATASET_DIRECTORIES.items():
            if (root / directory_name).exists():
                raise ValueError(
                    f"downloaded material is present for selected dataset: {dataset_id}"
                )


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


def _status_is_link_or_reparse(status: os.stat_result) -> bool:
    if stat.S_ISLNK(status.st_mode):
        return True
    file_attributes = getattr(status, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(file_attributes & reparse_attribute)


def _path_is_link_or_reparse(
    path: Path,
    *,
    status: os.stat_result | None = None,
) -> bool:
    if status is None:
        status = Path(path).lstat()
    return _status_is_link_or_reparse(status)


def _validate_trusted_component_chain(
    path: Path,
    *,
    trusted_root: Path = ROOT,
    final_must_be_directory: bool | None = None,
) -> bool:
    target = Path(path)
    anchor = Path(trusted_root)
    if not target.is_absolute() or not anchor.is_absolute():
        raise EvidencePublicationError(
            "candidate canonical path and trusted root must be absolute"
        )
    if ".." in target.parts or ".." in anchor.parts:
        raise EvidencePublicationError(
            "candidate canonical path contains parent traversal"
        )
    try:
        anchor_status = anchor.lstat()
    except OSError as exc:
        raise EvidencePublicationError(
            "candidate canonical trusted root could not be inspected"
        ) from exc
    if _path_is_link_or_reparse(anchor, status=anchor_status):
        raise EvidencePublicationError(
            "candidate canonical trusted root is a link or reparse point"
        )
    if not stat.S_ISDIR(anchor_status.st_mode):
        raise EvidencePublicationError(
            "candidate canonical trusted root is not a directory"
        )
    try:
        relative = target.relative_to(anchor)
    except ValueError as exc:
        raise EvidencePublicationError(
            "candidate canonical path is outside its trusted root"
        ) from exc

    current = anchor
    for index, part in enumerate(relative.parts):
        current /= part
        try:
            status = current.lstat()
        except FileNotFoundError:
            return False
        if _path_is_link_or_reparse(current, status=status):
            raise EvidencePublicationError(
                "candidate canonical component is a link or reparse point"
            )
        is_final = index == len(relative.parts) - 1
        if (
            not is_final
            or final_must_be_directory is True
        ) and not stat.S_ISDIR(status.st_mode):
            raise EvidencePublicationError(
                "candidate canonical component is not a directory"
            )
    return True


def _validate_canonical_pair_metadata(
    result_path: Path,
    report_path: Path,
    *,
    require_entries: bool = True,
    trusted_root: Path = ROOT,
) -> None:
    result_path = Path(result_path)
    report_path = Path(report_path)
    if result_path.parent != report_path.parent:
        raise EvidencePublicationError("candidate canonical directory mismatch")
    try:
        parent_present = _validate_trusted_component_chain(
            result_path.parent,
            trusted_root=trusted_root,
            final_must_be_directory=True,
        )
        if not parent_present:
            if require_entries:
                raise EvidencePublicationError(
                    "candidate canonical parent is missing"
                )
            return
        for path in (result_path, report_path):
            try:
                entry_status = path.lstat()
            except FileNotFoundError:
                if require_entries:
                    raise EvidencePublicationError(
                        "candidate canonical entry is missing"
                    )
                continue
            if _path_is_link_or_reparse(path, status=entry_status):
                raise EvidencePublicationError(
                    "candidate canonical entry is a link or reparse point"
                )
            if not stat.S_ISREG(entry_status.st_mode):
                raise EvidencePublicationError(
                    "candidate canonical entry is not a regular file"
                )
    except EvidencePublicationError:
        raise
    except OSError as exc:
        raise EvidencePublicationError(
            "unable to inspect candidate canonical metadata"
        ) from exc


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
def publication_lock(
    *,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
) -> Iterator[None]:
    recovery_dir = Path(recovery_dir)
    try:
        recovery_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise EvidencePublicationError(
            "unable to prepare evidence publication recovery directory"
        ) from exc
    try:
        handle = (recovery_dir / LOCK_NAME).open("a+b")
    except OSError as exc:
        raise EvidencePublicationError("unable to open evidence publication lock") from exc

    lock_acquired = False
    try:
        try:
            _acquire_os_lock(handle)
        except OSError as exc:
            raise EvidencePublicationError(
                "evidence publication lock is already held or unavailable"
            ) from exc
        lock_acquired = True
        yield
    finally:
        if lock_acquired:
            try:
                _release_os_lock(handle)
            except OSError:
                pass
        try:
            handle.close()
        except OSError:
            pass


def _validate_sha256(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise EvidencePublicationError(f"invalid publication transaction digest: {field}")
    return value


def _validate_transaction_id(value: Any) -> str:
    if not isinstance(value, str) or _TRANSACTION_ID_PATTERN.fullmatch(value) is None:
        raise EvidencePublicationError("invalid publication transaction id")
    return value


def _transaction_paths(recovery_dir: Path, transaction_id: str) -> dict[str, Path]:
    transaction_id = _validate_transaction_id(transaction_id)
    return {
        "new_result": recovery_dir / f"{transaction_id}.result.stage",
        "new_report": recovery_dir / f"{transaction_id}.report.stage",
        "previous_result": recovery_dir / f"{transaction_id}.result.backup",
        "previous_report": recovery_dir / f"{transaction_id}.report.backup",
        "restore_result": recovery_dir / f"{transaction_id}.result.restore",
        "restore_report": recovery_dir / f"{transaction_id}.report.restore",
        "journal_update": recovery_dir / f"{transaction_id}.journal.stage",
    }


def _write_text_fsynced(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline=None) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_bytes_fsynced(path: Path, content: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _discard_unjournaled_transaction(paths: dict[str, Path]) -> None:
    for path in paths.values():
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _cleanup_transaction(
    journal_path: Path,
    paths: dict[str, Path],
    *,
    receipt_path: Path | None = None,
) -> None:
    for path in paths.values():
        path.unlink(missing_ok=True)
    if receipt_path is not None:
        receipt_path.unlink(missing_ok=True)
    journal_path.unlink(missing_ok=True)


def _persist_journal_exclusively(journal_path: Path, transaction: dict[str, Any]) -> None:
    journal_created = False
    try:
        with journal_path.open("xb") as handle:
            journal_created = True
            handle.write(
                (json.dumps(transaction, indent=2, sort_keys=True) + "\n").encode("utf-8")
            )
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise
    except OSError:
        if journal_created:
            try:
                journal_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def _replace_journal_durably(
    journal_path: Path,
    transaction: dict[str, Any],
    paths: dict[str, Path],
) -> None:
    update_path = paths["journal_update"]
    update_path.unlink(missing_ok=True)
    _write_bytes_fsynced(
        update_path,
        (json.dumps(transaction, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    os.replace(update_path, journal_path)


def _load_transaction(journal_path: Path) -> dict[str, Any]:
    try:
        journal_bytes = journal_path.read_bytes()
    except OSError as exc:
        raise EvidencePublicationError("unable to read publication transaction journal") from exc
    if len(journal_bytes) > 16_384:
        raise EvidencePublicationError("publication transaction journal is too large")
    try:
        transaction = json.loads(journal_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidencePublicationError("invalid publication transaction journal") from exc
    if not isinstance(transaction, dict) or set(transaction) != {
        "schema_version",
        "transaction_id",
        "mode",
        "acceptance_status",
        "receipt_name",
        "previous_pair",
        "candidate_pair",
    }:
        raise EvidencePublicationError("invalid publication transaction fields")
    if (
        type(transaction["schema_version"]) is not int
        or transaction["schema_version"] != TRANSACTION_SCHEMA_VERSION
    ):
        raise EvidencePublicationError("unsupported publication transaction schema version")
    _validate_transaction_id(transaction["transaction_id"])
    if (
        not isinstance(transaction["mode"], str)
        or transaction["mode"] not in {"material-pending", "complete"}
    ):
        raise EvidencePublicationError("invalid publication transaction mode")
    if (
        not isinstance(transaction["acceptance_status"], str)
        or transaction["acceptance_status"] not in {
            "awaiting_acceptance",
            "accepted",
            "publishing",
        }
    ):
        raise EvidencePublicationError("invalid publication acceptance status")
    receipt_name = transaction["receipt_name"]
    if receipt_name is not None and (
        not isinstance(receipt_name, str)
        or _RECEIPT_NAME_PATTERN.fullmatch(receipt_name) is None
        or receipt_name in {JOURNAL_NAME, LOCK_NAME}
    ):
        raise EvidencePublicationError("invalid publication receipt name")
    if (
        transaction["acceptance_status"] == "awaiting_acceptance"
        and receipt_name is None
    ):
        raise EvidencePublicationError("awaiting publication transaction requires a receipt")
    if (
        transaction["acceptance_status"] == "publishing"
        and receipt_name is not None
    ):
        raise EvidencePublicationError("publishing transaction cannot record a receipt")

    previous_pair = transaction["previous_pair"]
    if not isinstance(previous_pair, dict) or set(previous_pair) != {
        "present",
        "result_sha256",
        "report_sha256",
    }:
        raise EvidencePublicationError("invalid previous-pair transaction fields")
    previous_present = previous_pair["present"]
    if type(previous_present) is not bool:
        raise EvidencePublicationError("invalid previous-pair presence flag")
    if previous_present:
        _validate_sha256(previous_pair["result_sha256"], field="previous result")
        _validate_sha256(previous_pair["report_sha256"], field="previous report")
    elif previous_pair["result_sha256"] is not None or previous_pair["report_sha256"] is not None:
        raise EvidencePublicationError("absent previous pair cannot record digests")

    candidate_pair = transaction["candidate_pair"]
    if not isinstance(candidate_pair, dict) or set(candidate_pair) != {
        "result_sha256",
        "report_sha256",
    }:
        raise EvidencePublicationError("invalid candidate-pair transaction fields")
    _validate_sha256(candidate_pair["result_sha256"], field="candidate result")
    _validate_sha256(candidate_pair["report_sha256"], field="candidate report")
    return transaction


def resolve_receipt_path(
    receipt_path: str | Path,
    *,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
) -> Path:
    if not isinstance(receipt_path, (str, Path)):
        raise EvidencePublicationError("publication receipt path must be path-like")
    raw = str(receipt_path)
    if not raw.strip() or "\x00" in raw or ".." in _raw_path_parts(raw):
        raise EvidencePublicationError("publication receipt path is invalid")
    try:
        candidate = Path(receipt_path).resolve(strict=False)
        expected_parent = Path(recovery_dir).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise EvidencePublicationError("publication receipt path is invalid") from exc
    if candidate.parent != expected_parent:
        raise EvidencePublicationError(
            "publication receipt must stay in the exact recovery directory"
        )
    if (
        _RECEIPT_NAME_PATTERN.fullmatch(candidate.name) is None
        or candidate.name in {JOURNAL_NAME, LOCK_NAME}
    ):
        raise EvidencePublicationError("publication receipt name is invalid")
    return candidate


def _receipt_from_transaction(transaction: Mapping[str, Any]) -> dict[str, Any]:
    previous_pair = transaction["previous_pair"]
    candidate_pair = transaction["candidate_pair"]
    return {
        "schema_version": transaction["schema_version"],
        "transaction_id": transaction["transaction_id"],
        "candidate_result_sha256": candidate_pair["result_sha256"],
        "candidate_report_sha256": candidate_pair["report_sha256"],
        "previous_pair_present": previous_pair["present"],
        "previous_result_sha256": previous_pair["result_sha256"],
        "previous_report_sha256": previous_pair["report_sha256"],
        "mode": transaction["mode"],
    }


def _load_receipt(receipt_path: Path) -> dict[str, Any]:
    try:
        receipt_bytes = receipt_path.read_bytes()
    except OSError as exc:
        raise EvidencePublicationError("unable to read publication receipt") from exc
    if len(receipt_bytes) > 8_192:
        raise EvidencePublicationError("publication receipt is too large")
    try:
        receipt = json.loads(receipt_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidencePublicationError("invalid publication receipt") from exc
    expected_fields = {
        "schema_version",
        "transaction_id",
        "candidate_result_sha256",
        "candidate_report_sha256",
        "previous_pair_present",
        "previous_result_sha256",
        "previous_report_sha256",
        "mode",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_fields:
        raise EvidencePublicationError("invalid publication receipt fields")
    if (
        type(receipt["schema_version"]) is not int
        or receipt["schema_version"] != TRANSACTION_SCHEMA_VERSION
    ):
        raise EvidencePublicationError("unsupported publication receipt schema version")
    _validate_transaction_id(receipt["transaction_id"])
    _validate_sha256(receipt["candidate_result_sha256"], field="receipt candidate result")
    _validate_sha256(receipt["candidate_report_sha256"], field="receipt candidate report")
    if type(receipt["previous_pair_present"]) is not bool:
        raise EvidencePublicationError("invalid receipt previous-pair presence flag")
    if receipt["previous_pair_present"]:
        _validate_sha256(receipt["previous_result_sha256"], field="receipt previous result")
        _validate_sha256(receipt["previous_report_sha256"], field="receipt previous report")
    elif (
        receipt["previous_result_sha256"] is not None
        or receipt["previous_report_sha256"] is not None
    ):
        raise EvidencePublicationError("absent receipt previous pair cannot record digests")
    if (
        not isinstance(receipt["mode"], str)
        or receipt["mode"] not in {"material-pending", "complete"}
    ):
        raise EvidencePublicationError("invalid publication receipt mode")
    return receipt


def _transaction_from_recovery_receipt(
    receipt_path: Path,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": receipt["schema_version"],
        "transaction_id": receipt["transaction_id"],
        "mode": receipt["mode"],
        "acceptance_status": "awaiting_acceptance",
        "receipt_name": receipt_path.name,
        "previous_pair": {
            "present": receipt["previous_pair_present"],
            "result_sha256": receipt["previous_result_sha256"],
            "report_sha256": receipt["previous_report_sha256"],
        },
        "candidate_pair": {
            "result_sha256": receipt["candidate_result_sha256"],
            "report_sha256": receipt["candidate_report_sha256"],
        },
    }


def _validate_receipt_recovery_artifacts(
    transaction: Mapping[str, Any],
    *,
    receipt_path: Path,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> None:
    recovery_dir = Path(recovery_dir)
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    required_names = {JOURNAL_NAME, receipt_path.name}
    allowed_names = set(required_names)
    previous_pair = transaction["previous_pair"]
    if previous_pair["present"]:
        allowed_names.update(
            {
                paths["previous_result"].name,
                paths["previous_report"].name,
            }
        )
    try:
        entries = list(recovery_dir.iterdir())
        resolved_recovery_dir = recovery_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise EvidencePublicationError(
            "unable to inspect receipt recovery artifacts"
        ) from exc
    actual_names = {entry.name for entry in entries}
    if not required_names.issubset(actual_names) or not actual_names.issubset(
        allowed_names | {LOCK_NAME}
    ):
        raise EvidencePublicationError(
            "receipt recovery requires one exact transaction artifact set"
        )
    for entry in entries:
        try:
            resolved_entry = entry.resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise EvidencePublicationError(
                "receipt recovery artifact path is invalid"
            ) from exc
        if resolved_entry.parent != resolved_recovery_dir or not resolved_entry.is_file():
            raise EvidencePublicationError(
                "receipt recovery artifact must be a contained regular file"
            )

    result_path = Path(result_path)
    report_path = Path(report_path)
    _validate_canonical_pair_metadata(
        result_path,
        report_path,
        require_entries=False,
        trusted_root=trusted_root,
    )
    if previous_pair["present"]:
        already_restored = _canonical_pair_matches_raw_digests(
            result_path,
            report_path,
            result_sha256=previous_pair["result_sha256"],
            report_sha256=previous_pair["report_sha256"],
            trusted_root=trusted_root,
        )
    else:
        already_restored = not result_path.exists() and not report_path.exists()

    if not already_restored:
        if actual_names.intersection(allowed_names) != allowed_names:
            raise EvidencePublicationError(
                "candidate receipt recovery requires every exact backup artifact"
            )
        _validated_candidate_payload(
            result_path=result_path,
            report_path=report_path,
            transaction=transaction,
            trusted_root=trusted_root,
        )
    if previous_pair["present"]:
        for backup_path, expected_digest, label in (
            (
                paths["previous_result"],
                previous_pair["result_sha256"],
                "result",
            ),
            (
                paths["previous_report"],
                previous_pair["report_sha256"],
                "report",
            ),
        ):
            if not backup_path.exists():
                if already_restored:
                    continue
                raise EvidencePublicationError(
                    f"required receipt recovery {label} backup is missing"
                )
            try:
                backup_bytes = backup_path.read_bytes()
            except OSError as exc:
                raise EvidencePublicationError(
                    f"unable to read receipt recovery {label} backup"
                ) from exc
            if _sha256_bytes(backup_bytes) != expected_digest:
                raise EvidencePublicationError(
                    f"receipt recovery {label} backup digest mismatch"
                )


def _load_receipt_recovery_transaction(
    receipt_path: str | Path,
    *,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> dict[str, Any]:
    recovery_dir = Path(recovery_dir)
    resolved_receipt = resolve_receipt_path(
        receipt_path,
        recovery_dir=recovery_dir,
    )
    receipt = _load_receipt(resolved_receipt)
    transaction = _transaction_from_recovery_receipt(resolved_receipt, receipt)
    _validate_receipt_recovery_artifacts(
        transaction,
        receipt_path=resolved_receipt,
        result_path=Path(result_path),
        report_path=Path(report_path),
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )
    return transaction


def _discover_receipt_recovery_transaction(
    *,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> dict[str, Any]:
    recovery_dir = Path(recovery_dir)
    try:
        entries = list(recovery_dir.iterdir())
    except OSError as exc:
        raise EvidencePublicationError(
            "unable to inspect publication receipt recovery directory"
        ) from exc
    receipt_paths = [
        entry
        for entry in entries
        if entry.name not in {JOURNAL_NAME, LOCK_NAME}
        and _RECEIPT_NAME_PATTERN.fullmatch(entry.name) is not None
    ]
    if len(receipt_paths) != 1:
        raise EvidencePublicationError(
            "journal recovery requires exactly one safe publication receipt"
        )
    return _load_receipt_recovery_transaction(
        receipt_paths[0],
        result_path=Path(result_path),
        report_path=Path(report_path),
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )


def _receipt_path_for_transaction(
    recovery_dir: Path,
    transaction: Mapping[str, Any],
) -> Path | None:
    receipt_name = transaction.get("receipt_name")
    if receipt_name is None:
        return None
    return resolve_receipt_path(
        Path(recovery_dir) / receipt_name,
        recovery_dir=recovery_dir,
    )


def _validate_receipt_matches_transaction(
    receipt: Mapping[str, Any],
    transaction: Mapping[str, Any],
) -> None:
    if dict(receipt) != _receipt_from_transaction(transaction):
        raise EvidencePublicationError("publication receipt does not match live transaction")


def verify_evidence_pair_bytes(
    result_bytes: bytes,
    report_bytes: bytes,
    *,
    expected_result_sha256: str | None = None,
    expected_report_sha256: str | None = None,
) -> None:
    if not isinstance(result_bytes, bytes) or not isinstance(report_bytes, bytes):
        raise EvidencePublicationError("evidence pair verification requires exact bytes")
    result_sha256 = _sha256_bytes(result_bytes)
    report_sha256 = _sha256_bytes(report_bytes)
    if expected_result_sha256 is not None:
        _validate_sha256(expected_result_sha256, field="expected result")
        if result_sha256 != expected_result_sha256:
            raise EvidencePublicationError("published result digest mismatch")
    if expected_report_sha256 is not None:
        _validate_sha256(expected_report_sha256, field="expected report")
        if report_sha256 != expected_report_sha256:
            raise EvidencePublicationError("published report digest mismatch")
    try:
        report_text = report_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise EvidencePublicationError("published report is not valid UTF-8") from exc
    markers = _REPORT_COMMIT_MARKER_PATTERN.findall(report_text)
    if len(markers) != 1 or markers[0] != result_sha256:
        raise EvidencePublicationError("publication commit marker does not match result bytes")


def recover_incomplete_publication(
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
    trusted_root: Path = ROOT,
) -> str:
    result_path = Path(result_path)
    report_path = Path(report_path)
    recovery_dir = Path(recovery_dir)
    journal_path = recovery_dir / JOURNAL_NAME
    if not journal_path.exists():
        return "none"

    try:
        transaction = _load_transaction(journal_path)
    except EvidencePublicationError as journal_error:
        try:
            recovery_transaction = _discover_receipt_recovery_transaction(
                result_path=result_path,
                report_path=report_path,
                recovery_dir=recovery_dir,
                trusted_root=trusted_root,
            )
            return _force_restore_transaction(
                recovery_transaction,
                result_path=result_path,
                report_path=report_path,
                recovery_dir=recovery_dir,
                trusted_root=trusted_root,
            )
        except (EvidencePublicationError, OSError) as recovery_error:
            raise EvidencePublicationError(
                "invalid publication transaction journal; receipt recovery failed; "
                "evidence retained"
            ) from recovery_error
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    receipt_path = _receipt_path_for_transaction(recovery_dir, transaction)

    try:
        if transaction["acceptance_status"] == "accepted":
            try:
                _finish_accepted_transaction(
                    transaction,
                    result_path=result_path,
                    report_path=report_path,
                    recovery_dir=recovery_dir,
                    trusted_root=trusted_root,
                )
            except (EvidencePublicationError, OSError) as exc:
                raise EvidencePublicationError(
                    "accepted publication validation failed; "
                    "accepted evidence retained"
                ) from exc
            return "committed"
        if transaction["acceptance_status"] == "publishing":
            try:
                _validated_candidate_payload(
                    result_path=result_path,
                    report_path=report_path,
                    transaction=transaction,
                    trusted_root=trusted_root,
                )
            except EvidencePublicationError:
                pass
            else:
                transaction["acceptance_status"] = "accepted"
                _replace_journal_durably(journal_path, transaction, paths)
                _finish_accepted_transaction(
                    transaction,
                    result_path=result_path,
                    report_path=report_path,
                    recovery_dir=recovery_dir,
                    trusted_root=trusted_root,
                )
                return "committed"
        return _force_restore_transaction(
            transaction,
            result_path=result_path,
            report_path=report_path,
            recovery_dir=recovery_dir,
            trusted_root=trusted_root,
        )
    except EvidencePublicationError:
        raise
    except OSError as exc:
        raise EvidencePublicationError(
            "publication recovery failed; transaction retained"
        ) from exc


def _canonical_pair_matches_raw_digests(
    result_path: Path,
    report_path: Path,
    *,
    result_sha256: str,
    report_sha256: str,
    trusted_root: Path = ROOT,
) -> bool:
    _validate_canonical_pair_metadata(
        result_path,
        report_path,
        require_entries=False,
        trusted_root=trusted_root,
    )
    if not os.path.lexists(result_path) or not os.path.lexists(report_path):
        return False
    return (
        _sha256_bytes(result_path.read_bytes()) == result_sha256
        and _sha256_bytes(report_path.read_bytes()) == report_sha256
    )


def _force_restore_transaction(
    transaction: Mapping[str, Any],
    *,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> str:
    result_path = Path(result_path)
    report_path = Path(report_path)
    recovery_dir = Path(recovery_dir)
    journal_path = recovery_dir / JOURNAL_NAME
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    receipt_path = _receipt_path_for_transaction(recovery_dir, transaction)
    previous_pair = transaction["previous_pair"]
    candidate_pair = transaction["candidate_pair"]
    _validate_canonical_pair_metadata(
        result_path,
        report_path,
        require_entries=False,
        trusted_root=trusted_root,
    )

    if previous_pair["present"]:
        if _canonical_pair_matches_raw_digests(
            result_path,
            report_path,
            result_sha256=previous_pair["result_sha256"],
            report_sha256=previous_pair["report_sha256"],
            trusted_root=trusted_root,
        ):
            _cleanup_transaction(
                journal_path,
                paths,
                receipt_path=receipt_path,
            )
            return "restored"
        try:
            previous_result_bytes = paths["previous_result"].read_bytes()
            previous_report_bytes = paths["previous_report"].read_bytes()
        except OSError as exc:
            raise EvidencePublicationError("required publication backup is missing") from exc
        if _sha256_bytes(previous_result_bytes) != previous_pair["result_sha256"]:
            raise EvidencePublicationError("result backup digest mismatch")
        if _sha256_bytes(previous_report_bytes) != previous_pair["report_sha256"]:
            raise EvidencePublicationError("report backup digest mismatch")
        paths["restore_result"].unlink(missing_ok=True)
        paths["restore_report"].unlink(missing_ok=True)
        _write_bytes_fsynced(paths["restore_result"], previous_result_bytes)
        _write_bytes_fsynced(paths["restore_report"], previous_report_bytes)
        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=False,
            trusted_root=trusted_root,
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=False,
            trusted_root=trusted_root,
        )
        os.replace(paths["restore_result"], result_path)
        os.replace(paths["restore_report"], report_path)
        if not _canonical_pair_matches_raw_digests(
            result_path,
            report_path,
            result_sha256=previous_pair["result_sha256"],
            report_sha256=previous_pair["report_sha256"],
            trusted_root=trusted_root,
        ):
            raise EvidencePublicationError("restored publication pair digest mismatch")
    else:
        for canonical_path, expected_digest, label in (
            (result_path, candidate_pair["result_sha256"], "result"),
            (report_path, candidate_pair["report_sha256"], "report"),
        ):
            if os.path.lexists(canonical_path) and (
                _sha256_bytes(canonical_path.read_bytes()) != expected_digest
            ):
                raise EvidencePublicationError(
                    f"cannot restore absent previous pair: unexpected {label} bytes"
                )
        result_path.unlink(missing_ok=True)
        report_path.unlink(missing_ok=True)
        if os.path.lexists(result_path) or os.path.lexists(report_path):
            raise EvidencePublicationError("unable to restore absent previous pair")

    _cleanup_transaction(
        journal_path,
        paths,
        receipt_path=receipt_path,
    )
    return "restored"


def _validated_candidate_payload(
    *,
    result_path: Path,
    report_path: Path,
    transaction: Mapping[str, Any],
    trusted_root: Path = ROOT,
) -> dict[str, Any]:
    result_path = Path(result_path)
    report_path = Path(report_path)
    _validate_canonical_pair_metadata(
        result_path,
        report_path,
        trusted_root=trusted_root,
    )
    try:
        canonical_names = {path.name for path in result_path.parent.iterdir()}
    except OSError as exc:
        raise EvidencePublicationError("unable to inspect candidate canonical directory") from exc
    if canonical_names != {result_path.name, report_path.name}:
        raise EvidencePublicationError(
            "candidate canonical directory must contain exactly result and report"
        )
    try:
        result_bytes = result_path.read_bytes()
        report_bytes = report_path.read_bytes()
    except OSError as exc:
        raise EvidencePublicationError("unable to read candidate publication pair") from exc
    candidate_pair = transaction["candidate_pair"]
    verify_evidence_pair_bytes(
        result_bytes,
        report_bytes,
        expected_result_sha256=candidate_pair["result_sha256"],
        expected_report_sha256=candidate_pair["report_sha256"],
    )
    try:
        payload = json.loads(result_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidencePublicationError("candidate result is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise EvidencePublicationError("candidate result must be a JSON object")
    expected_payload_mode = transaction["mode"].replace("-", "_")
    if payload.get("mode") != expected_payload_mode:
        raise EvidencePublicationError("candidate result mode mismatch")
    try:
        if transaction["mode"] == "complete":
            validate_complete_payload(payload, root=trusted_root)
        else:
            validate_material_pending_payload(payload)
    except (TypeError, ValueError) as exc:
        raise EvidencePublicationError(
            f"candidate {transaction['mode']} payload is invalid: {exc}"
        ) from exc
    result_sha256 = _sha256_bytes(result_bytes)
    try:
        expected_report = render_phase_a_report(payload, result_sha256=result_sha256)
        actual_report = report_bytes.decode("utf-8")
    except (KeyError, TypeError, UnicodeError, ValueError) as exc:
        raise EvidencePublicationError("candidate report cannot be reproduced") from exc
    expected_report_on_disk = expected_report.replace("\n", os.linesep)
    if actual_report != expected_report_on_disk:
        raise EvidencePublicationError("candidate report is not a deterministic readback")
    return payload


def validate_candidate_evidence_pair(
    receipt_path: str | Path,
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
    trusted_root: Path = ROOT,
) -> dict[str, Any]:
    recovery_dir = Path(recovery_dir)
    resolved_receipt = resolve_receipt_path(
        receipt_path,
        recovery_dir=recovery_dir,
    )
    transaction = _load_transaction(recovery_dir / JOURNAL_NAME)
    if transaction["acceptance_status"] != "awaiting_acceptance":
        raise EvidencePublicationError("candidate transaction is not awaiting acceptance")
    if transaction["receipt_name"] != resolved_receipt.name:
        raise EvidencePublicationError("candidate receipt path does not match live transaction")
    receipt = _load_receipt(resolved_receipt)
    _validate_receipt_matches_transaction(receipt, transaction)
    _validate_receipt_recovery_artifacts(
        transaction,
        receipt_path=resolved_receipt,
        result_path=Path(result_path),
        report_path=Path(report_path),
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )
    return _validated_candidate_payload(
        result_path=result_path,
        report_path=report_path,
        transaction=transaction,
        trusted_root=trusted_root,
    )


def publish_evidence_pair(
    payload: dict[str, Any],
    *,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> None:
    """Publish an immediate synthetic pair; canonical targets require acceptance."""

    _write_evidence_pair_transaction(
        payload,
        mode="material-pending",
        receipt_path=None,
        result_path=result_path,
        report_path=report_path,
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )


def stage_evidence_pair(
    payload: dict[str, Any],
    *,
    mode: str,
    receipt_path: str | Path,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
    trusted_root: Path = ROOT,
) -> dict[str, Any]:
    receipt = _write_evidence_pair_transaction(
        payload,
        mode=mode,
        receipt_path=receipt_path,
        result_path=result_path,
        report_path=report_path,
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )
    if receipt is None:
        raise EvidencePublicationError("deferred publication did not produce a receipt")
    return receipt


def _write_evidence_pair_transaction(
    payload: dict[str, Any],
    *,
    mode: str,
    receipt_path: str | Path | None,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    trusted_root: Path = ROOT,
) -> dict[str, Any] | None:
    if not isinstance(mode, str) or mode not in {"material-pending", "complete"}:
        raise EvidencePublicationError("invalid evidence publication mode")
    try:
        if mode == "complete":
            validate_complete_payload(payload, root=trusted_root)
        else:
            validate_material_pending_payload(payload)
    except (TypeError, ValueError) as exc:
        raise EvidencePublicationError(
            f"{mode} payload is invalid: {exc}"
        ) from exc
    result_path = Path(result_path)
    report_path = Path(report_path)
    recovery_dir = Path(recovery_dir)
    if result_path == report_path:
        raise EvidencePublicationError("result and report paths must be distinct")
    _validate_canonical_pair_metadata(
        result_path,
        report_path,
        require_entries=False,
        trusted_root=trusted_root,
    )
    if receipt_path is None:
        try:
            lexical_targets = {
                Path(os.path.abspath(result_path)),
                Path(os.path.abspath(report_path)),
            }
            canonical_targets = {
                Path(os.path.abspath(DEFAULT_RESULT)),
                Path(os.path.abspath(DEFAULT_REPORT)),
            }
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise EvidencePublicationError(
                "immediate evidence publication paths are invalid"
            ) from exc
        if lexical_targets & canonical_targets:
            raise EvidencePublicationError(
                "canonical evidence publication requires deferred acceptance"
            )
    resolved_receipt: Path | None = None
    if receipt_path is not None:
        resolved_receipt = resolve_receipt_path(
            receipt_path,
            recovery_dir=recovery_dir,
        )
        if resolved_receipt.exists():
            raise EvidencePublicationError("publication receipt already exists")

    try:
        recovery_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise EvidencePublicationError(
            "unable to prepare evidence publication recovery directory"
        ) from exc
    journal_path = recovery_dir / JOURNAL_NAME
    if journal_path.exists():
        raise EvidencePublicationError("an evidence publication transaction is already active")
    transaction_id = uuid.uuid4().hex
    paths = _transaction_paths(recovery_dir, transaction_id)
    journal_durable = False

    try:
        result_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        _write_text_fsynced(paths["new_result"], result_text)
        result_sha256 = _sha256_bytes(paths["new_result"].read_bytes())
        report_text = render_phase_a_report(payload, result_sha256=result_sha256)
        _write_text_fsynced(paths["new_report"], report_text)
        report_sha256 = _sha256_bytes(paths["new_report"].read_bytes())

        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=False,
            trusted_root=trusted_root,
        )
        result_exists = os.path.lexists(result_path)
        report_exists = os.path.lexists(report_path)
        if result_exists != report_exists:
            raise EvidencePublicationError("partial pre-existing evidence pair")
        previous_result_sha256: str | None = None
        previous_report_sha256: str | None = None
        if result_exists:
            previous_result_bytes = result_path.read_bytes()
            previous_report_bytes = report_path.read_bytes()
            _write_bytes_fsynced(paths["previous_result"], previous_result_bytes)
            _write_bytes_fsynced(paths["previous_report"], previous_report_bytes)
            previous_result_sha256 = _sha256_bytes(previous_result_bytes)
            previous_report_sha256 = _sha256_bytes(previous_report_bytes)

        transaction = {
            "schema_version": TRANSACTION_SCHEMA_VERSION,
            "transaction_id": transaction_id,
            "mode": mode,
            "acceptance_status": (
                "awaiting_acceptance" if resolved_receipt is not None else "publishing"
            ),
            "receipt_name": (
                resolved_receipt.name if resolved_receipt is not None else None
            ),
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
        _persist_journal_exclusively(journal_path, transaction)
        journal_durable = True

        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=False,
            trusted_root=trusted_root,
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=False,
            trusted_root=trusted_root,
        )
        os.replace(paths["new_result"], result_path)
        os.replace(paths["new_report"], report_path)
        _validate_canonical_pair_metadata(
            result_path,
            report_path,
            require_entries=True,
            trusted_root=trusted_root,
        )
        verify_evidence_pair_bytes(
            result_path.read_bytes(),
            report_path.read_bytes(),
            expected_result_sha256=result_sha256,
            expected_report_sha256=report_sha256,
        )
        if resolved_receipt is not None:
            receipt = _receipt_from_transaction(transaction)
            _write_bytes_fsynced(
                resolved_receipt,
                (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            return receipt
        transaction["acceptance_status"] = "accepted"
        _replace_journal_durably(journal_path, transaction, paths)
        _cleanup_transaction(journal_path, paths)
        return None
    except EvidencePublicationError:
        if not journal_durable:
            _discard_unjournaled_transaction(paths)
        raise
    except OSError as exc:
        if journal_durable:
            try:
                recovery_result = recover_incomplete_publication(
                    result_path=result_path,
                    report_path=report_path,
                    recovery_dir=recovery_dir,
                    trusted_root=trusted_root,
                )
            except EvidencePublicationError as recovery_exc:
                raise EvidencePublicationError(
                    "evidence publication failed and immediate recovery failed"
                ) from recovery_exc
            raise EvidencePublicationError(
                f"evidence publication failed; immediate recovery {recovery_result}"
            ) from exc
        _discard_unjournaled_transaction(paths)
        raise EvidencePublicationError("evidence publication failed before commit") from exc


def _load_live_receipt_transaction(
    receipt_path: str | Path,
    *,
    recovery_dir: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    recovery_dir = Path(recovery_dir)
    resolved_receipt = resolve_receipt_path(
        receipt_path,
        recovery_dir=recovery_dir,
    )
    transaction = _load_transaction(recovery_dir / JOURNAL_NAME)
    if transaction["receipt_name"] != resolved_receipt.name:
        raise EvidencePublicationError("receipt path does not match live transaction")
    receipt = _load_receipt(resolved_receipt)
    _validate_receipt_matches_transaction(receipt, transaction)
    return resolved_receipt, receipt, transaction


def _finish_accepted_transaction(
    transaction: Mapping[str, Any],
    *,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    supplied_receipt_path: str | Path | None = None,
    trusted_root: Path = ROOT,
) -> None:
    if transaction["acceptance_status"] != "accepted":
        raise EvidencePublicationError("publication transaction is not accepted")
    recovery_dir = Path(recovery_dir)
    expected_receipt = _receipt_path_for_transaction(recovery_dir, transaction)
    if supplied_receipt_path is not None:
        resolved_receipt = resolve_receipt_path(
            supplied_receipt_path,
            recovery_dir=recovery_dir,
        )
        if expected_receipt is None or resolved_receipt.name != expected_receipt.name:
            raise EvidencePublicationError(
                "receipt path does not match accepted transaction"
            )
    else:
        resolved_receipt = expected_receipt
    if resolved_receipt is not None and resolved_receipt.exists():
        _validate_receipt_matches_transaction(
            _load_receipt(resolved_receipt),
            transaction,
        )
    _validated_candidate_payload(
        result_path=Path(result_path),
        report_path=Path(report_path),
        transaction=transaction,
        trusted_root=trusted_root,
    )
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    _cleanup_transaction(
        recovery_dir / JOURNAL_NAME,
        paths,
        receipt_path=expected_receipt,
    )


def accept_evidence_receipt(
    receipt_path: str | Path,
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
    trusted_root: Path = ROOT,
) -> None:
    recovery_dir = Path(recovery_dir)
    journal_path = recovery_dir / JOURNAL_NAME
    transaction: dict[str, Any] | None = None
    try:
        transaction = _load_transaction(journal_path)
    except EvidencePublicationError as journal_error:
        try:
            recovery_transaction = _load_receipt_recovery_transaction(
                receipt_path,
                result_path=Path(result_path),
                report_path=Path(report_path),
                recovery_dir=recovery_dir,
                trusted_root=trusted_root,
            )
            _force_restore_transaction(
                recovery_transaction,
                result_path=Path(result_path),
                report_path=Path(report_path),
                recovery_dir=recovery_dir,
                trusted_root=trusted_root,
            )
        except (EvidencePublicationError, OSError) as restore_error:
            raise EvidencePublicationError(
                "publication acceptance requires a valid matching journal; "
                "receipt restoration failed; evidence retained"
            ) from restore_error
        raise EvidencePublicationError(
            "publication acceptance requires a valid matching journal; "
            "previous pair restored"
        ) from journal_error

    if transaction["acceptance_status"] == "accepted":
        try:
            _finish_accepted_transaction(
                transaction,
                result_path=Path(result_path),
                report_path=Path(report_path),
                recovery_dir=recovery_dir,
                supplied_receipt_path=receipt_path,
                trusted_root=trusted_root,
            )
        except OSError as exc:
            raise EvidencePublicationError(
                "accepted publication cleanup failed; accepted evidence retained"
            ) from exc
        return

    try:
        _resolved_receipt, _receipt, loaded_transaction = _load_live_receipt_transaction(
            receipt_path,
            recovery_dir=recovery_dir,
        )
        if loaded_transaction != transaction:
            raise EvidencePublicationError(
                "publication transaction changed during acceptance"
            )
        if transaction["acceptance_status"] != "awaiting_acceptance":
            raise EvidencePublicationError("publication transaction is not awaiting acceptance")
        _validate_receipt_recovery_artifacts(
            transaction,
            receipt_path=_resolved_receipt,
            result_path=Path(result_path),
            report_path=Path(report_path),
            recovery_dir=recovery_dir,
            trusted_root=trusted_root,
        )
        _validated_candidate_payload(
            result_path=Path(result_path),
            report_path=Path(report_path),
            transaction=transaction,
            trusted_root=trusted_root,
        )
    except (EvidencePublicationError, OSError) as exc:
        if transaction is not None:
            try:
                _force_restore_transaction(
                    transaction,
                    result_path=Path(result_path),
                    report_path=Path(report_path),
                    recovery_dir=recovery_dir,
                    trusted_root=trusted_root,
                )
            except (EvidencePublicationError, OSError) as restore_exc:
                raise EvidencePublicationError(
                    "publication acceptance failed and previous-pair restoration failed"
                ) from restore_exc
        if isinstance(exc, EvidencePublicationError):
            raise
        raise EvidencePublicationError("publication acceptance failed") from exc

    transaction["acceptance_status"] = "accepted"
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    _replace_journal_durably(journal_path, transaction, paths)
    _cleanup_transaction(
        journal_path,
        paths,
        receipt_path=resolve_receipt_path(receipt_path, recovery_dir=recovery_dir),
    )


def reject_evidence_receipt(
    receipt_path: str | Path,
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
    trusted_root: Path = ROOT,
) -> None:
    recovery_dir = Path(recovery_dir)
    try:
        transaction = _load_transaction(recovery_dir / JOURNAL_NAME)
    except EvidencePublicationError:
        recovery_transaction = _load_receipt_recovery_transaction(
            receipt_path,
            result_path=Path(result_path),
            report_path=Path(report_path),
            recovery_dir=recovery_dir,
            trusted_root=trusted_root,
        )
        _force_restore_transaction(
            recovery_transaction,
            result_path=Path(result_path),
            report_path=Path(report_path),
            recovery_dir=recovery_dir,
            trusted_root=trusted_root,
        )
        return
    if transaction["acceptance_status"] == "accepted":
        try:
            _finish_accepted_transaction(
                transaction,
                result_path=Path(result_path),
                report_path=Path(report_path),
                recovery_dir=recovery_dir,
                supplied_receipt_path=receipt_path,
                trusted_root=trusted_root,
            )
        except OSError as exc:
            raise EvidencePublicationError(
                "accepted publication cleanup failed; accepted evidence retained"
            ) from exc
        raise EvidencePublicationError(
            "accepted publication transaction cannot be rejected"
        )
    receipt_error: EvidencePublicationError | None = None
    try:
        resolved_receipt = resolve_receipt_path(
            receipt_path,
            recovery_dir=recovery_dir,
        )
        if transaction["receipt_name"] != resolved_receipt.name:
            raise EvidencePublicationError("receipt path does not match live transaction")
        _validate_receipt_matches_transaction(
            _load_receipt(resolved_receipt),
            transaction,
        )
    except EvidencePublicationError as exc:
        receipt_error = exc
    _force_restore_transaction(
        transaction,
        result_path=Path(result_path),
        report_path=Path(report_path),
        recovery_dir=recovery_dir,
        trusted_root=trusted_root,
    )
    if receipt_error is not None:
        raise receipt_error


def stage_verified_candidate(
    *,
    root: Path,
    case_path: Path,
    result_path: Path,
    report_path: Path,
    recovery_dir: Path,
    receipt_path: Path,
    material_root: Path,
    baseline_commit: str,
    head_commit: str,
    mode: str,
) -> dict[str, Any]:
    if not isinstance(mode, str) or mode not in {"material-pending", "complete"}:
        raise ValueError("invalid evidence verification mode")
    root = Path(root)
    recovery_dir = Path(recovery_dir)
    if (
        not isinstance(head_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", head_commit) is None
    ):
        raise ValueError("expected repository HEAD must be lowercase 40-hex")
    first_material_error: OSError | ValueError | None = None
    if mode == "material-pending":
        try:
            validate_material_pending_dataset_absence(material_root)
        except (OSError, ValueError) as exc:
            first_material_error = exc
    with publication_lock(recovery_dir=recovery_dir):
        recover_incomplete_publication(
            result_path=result_path,
            report_path=report_path,
            recovery_dir=recovery_dir,
            trusted_root=root,
        )
    if first_material_error is not None:
        raise first_material_error
    _assert_repository_head(root, expected_head=head_commit)
    prepared = prepare_verification_evidence(
        root,
        baseline_commit,
        head_commit,
        mode,
    )
    with persistent_verification_lock(
        prepared,
        root=root,
        recovery_dir=recovery_dir,
    ) as capability:
        recover_incomplete_publication(
            result_path=result_path,
            report_path=report_path,
            recovery_dir=recovery_dir,
            trusted_root=root,
        )
        verification_evidence = finalize_verification_evidence(
            prepared,
            root=root,
            capability=capability,
        )
        payload = build_phase_a_payload(
            case_path,
            root=root,
            verification_evidence=verification_evidence,
            mode=mode.replace("-", "_"),
        )
        _assert_repository_head(root, expected_head=head_commit)
        validate_active_verification_lock(
            prepared,
            root=root,
            capability=capability,
        )
        if mode == "material-pending":
            validate_material_pending_dataset_absence(material_root)
        return stage_evidence_pair(
            payload,
            mode=mode,
            receipt_path=receipt_path,
            result_path=result_path,
            report_path=report_path,
            recovery_dir=recovery_dir,
            trusted_root=root,
        )


def _current_repository_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("unable to capture current input HEAD")
    head = completed.stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise ValueError("current input HEAD is not canonical lowercase Git hex")
    return head


def _assert_repository_head(root: Path, *, expected_head: str) -> None:
    if (
        not isinstance(expected_head, str)
        or re.fullmatch(r"[0-9a-f]{40}", expected_head) is None
    ):
        raise ValueError("expected repository HEAD must be lowercase 40-hex")
    if _current_repository_head(root) != expected_head:
        raise ValueError("repository HEAD changed during evidence publication")


def main(
    argv: Sequence[str] | None = None,
    *,
    material_root: Path | None = None,
) -> int:
    args = parse_args(argv)
    try:
        case_path = resolve_project_path(args.case, allowed_root=DEFAULT_CASE.parent)
        result_path = resolve_project_path(
            args.out,
            allowed_root=DEFAULT_OUTPUT_DIR,
            inspect_lexical_chain=True,
        )
        report_path = resolve_project_path(
            args.report_out,
            allowed_root=DEFAULT_OUTPUT_DIR,
            inspect_lexical_chain=True,
        )
        if result_path == report_path:
            raise ValueError("result and report paths must be distinct")
        if result_path != Path(os.path.abspath(DEFAULT_RESULT)):
            raise ValueError("result path must be the fixed lexical result destination")
        if report_path != Path(os.path.abspath(DEFAULT_REPORT)):
            raise ValueError("report path must be the fixed lexical report destination")
        if args.accept_receipt is not None:
            receipt_path = resolve_receipt_path(
                args.accept_receipt,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
            with publication_lock(recovery_dir=DEFAULT_RECOVERY_DIR):
                accept_evidence_receipt(
                    receipt_path,
                    result_path=result_path,
                    report_path=report_path,
                    recovery_dir=DEFAULT_RECOVERY_DIR,
                    trusted_root=ROOT,
                )
            output: dict[str, Any] = {"acceptance_status": "accepted"}
        elif args.reject_receipt is not None:
            receipt_path = resolve_receipt_path(
                args.reject_receipt,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
            with publication_lock(recovery_dir=DEFAULT_RECOVERY_DIR):
                reject_evidence_receipt(
                    receipt_path,
                    result_path=result_path,
                    report_path=report_path,
                    recovery_dir=DEFAULT_RECOVERY_DIR,
                    trusted_root=ROOT,
                )
            output = {"acceptance_status": "rejected"}
        else:
            if material_root is None:
                material_root = DEFAULT_MATERIAL_ROOT
            receipt_path = resolve_receipt_path(
                args.receipt,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
            output = stage_verified_candidate(
                root=ROOT,
                case_path=case_path,
                result_path=result_path,
                report_path=report_path,
                recovery_dir=DEFAULT_RECOVERY_DIR,
                receipt_path=receipt_path,
                material_root=material_root,
                baseline_commit=IMPLEMENTATION_BASELINE_COMMIT,
                head_commit=_current_repository_head(ROOT),
                mode=args.mode,
            )
    except (
        EvidencePublicationError,
        OSError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"EMOTION-STATE-001 evidence publication failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
