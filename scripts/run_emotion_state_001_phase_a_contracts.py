#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
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
    build_phase_a_payload,
    render_phase_a_report,
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
JOURNAL_NAME = "transaction.json"
LOCK_NAME = "publication.lock"
TRANSACTION_SCHEMA_VERSION = 1
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
_TRANSACTION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_REPORT_COMMIT_MARKER_PATTERN = re.compile(
    r"(?m)^- Publication commit marker: `result\.json sha256:([0-9A-F]{64})`\r?$"
)


class EvidencePublicationError(RuntimeError):
    """A bounded, recoverable evidence-publication failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build EMOTION-STATE-001 Phase A contract evidence."
    )
    parser.add_argument("--case", default=str(DEFAULT_CASE))
    parser.add_argument("--out", default=str(DEFAULT_RESULT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    return parser.parse_args()


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


def resolve_project_path(path_value: str, *, allowed_root: Path) -> Path:
    if not isinstance(path_value, str) or not path_value.strip() or "\x00" in path_value:
        raise ValueError("path must be a non-empty string")
    raw_parts = _raw_path_parts(path_value)
    if ".." in raw_parts:
        raise ValueError(f"parent traversal is blocked: {path_value}")
    if _contains_private_parts(raw_parts):
        raise ValueError(f"private path is blocked: {path_value}")
    try:
        candidate = Path(path_value)
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
    return resolved


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


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


def _cleanup_transaction(journal_path: Path, paths: dict[str, Path]) -> None:
    for path in paths.values():
        path.unlink(missing_ok=True)
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
        "previous_pair",
        "new_pair",
    }:
        raise EvidencePublicationError("invalid publication transaction fields")
    if (
        type(transaction["schema_version"]) is not int
        or transaction["schema_version"] != TRANSACTION_SCHEMA_VERSION
    ):
        raise EvidencePublicationError("unsupported publication transaction schema version")
    _validate_transaction_id(transaction["transaction_id"])

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

    new_pair = transaction["new_pair"]
    if not isinstance(new_pair, dict) or set(new_pair) != {
        "result_sha256",
        "report_sha256",
    }:
        raise EvidencePublicationError("invalid new-pair transaction fields")
    _validate_sha256(new_pair["result_sha256"], field="new result")
    _validate_sha256(new_pair["report_sha256"], field="new report")
    return transaction


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
) -> str:
    result_path = Path(result_path)
    report_path = Path(report_path)
    recovery_dir = Path(recovery_dir)
    journal_path = recovery_dir / JOURNAL_NAME
    if not journal_path.exists():
        return "none"

    transaction = _load_transaction(journal_path)
    paths = _transaction_paths(recovery_dir, transaction["transaction_id"])
    new_pair = transaction["new_pair"]
    previous_pair = transaction["previous_pair"]

    try:
        if result_path.exists() and report_path.exists():
            result_bytes = result_path.read_bytes()
            report_bytes = report_path.read_bytes()
            try:
                verify_evidence_pair_bytes(
                    result_bytes,
                    report_bytes,
                    expected_result_sha256=new_pair["result_sha256"],
                    expected_report_sha256=new_pair["report_sha256"],
                )
            except EvidencePublicationError:
                pass
            else:
                _cleanup_transaction(journal_path, paths)
                return "committed"
            if (
                previous_pair["present"]
                and _sha256_bytes(result_bytes) == previous_pair["result_sha256"]
                and _sha256_bytes(report_bytes) == previous_pair["report_sha256"]
            ):
                _cleanup_transaction(journal_path, paths)
                return "restored"

        if previous_pair["present"]:
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
            result_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(paths["restore_result"], result_path)
            os.replace(paths["restore_report"], report_path)
            if _sha256_bytes(result_path.read_bytes()) != previous_pair["result_sha256"]:
                raise EvidencePublicationError("restored result digest mismatch")
            if _sha256_bytes(report_path.read_bytes()) != previous_pair["report_sha256"]:
                raise EvidencePublicationError("restored report digest mismatch")
        else:
            for canonical_path, expected_digest, label in (
                (result_path, new_pair["result_sha256"], "result"),
                (report_path, new_pair["report_sha256"], "report"),
            ):
                if canonical_path.exists():
                    if _sha256_bytes(canonical_path.read_bytes()) != expected_digest:
                        raise EvidencePublicationError(
                            f"cannot restore absent previous pair: unexpected {label} bytes"
                        )
            result_path.unlink(missing_ok=True)
            report_path.unlink(missing_ok=True)
            if result_path.exists() or report_path.exists():
                raise EvidencePublicationError("unable to restore absent previous pair")

        _cleanup_transaction(journal_path, paths)
        return "restored"
    except EvidencePublicationError:
        raise
    except OSError as exc:
        raise EvidencePublicationError("publication recovery failed; transaction retained") from exc


def publish_evidence_pair(
    payload: dict[str, Any],
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    recovery_dir: Path = DEFAULT_RECOVERY_DIR,
) -> None:
    result_path = Path(result_path)
    report_path = Path(report_path)
    recovery_dir = Path(recovery_dir)
    if result_path == report_path:
        raise EvidencePublicationError("result and report paths must be distinct")

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

        result_exists = result_path.exists()
        report_exists = report_path.exists()
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
            "previous_pair": {
                "present": result_exists,
                "result_sha256": previous_result_sha256,
                "report_sha256": previous_report_sha256,
            },
            "new_pair": {
                "result_sha256": result_sha256,
                "report_sha256": report_sha256,
            },
        }
        _persist_journal_exclusively(journal_path, transaction)
        journal_durable = True

        result_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(paths["new_result"], result_path)
        os.replace(paths["new_report"], report_path)
        verify_evidence_pair_bytes(
            result_path.read_bytes(),
            report_path.read_bytes(),
            expected_result_sha256=result_sha256,
            expected_report_sha256=report_sha256,
        )
        _cleanup_transaction(journal_path, paths)
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


def main() -> int:
    args = parse_args()
    try:
        case_path = resolve_project_path(args.case, allowed_root=DEFAULT_CASE.parent)
        result_path = resolve_project_path(args.out, allowed_root=DEFAULT_OUTPUT_DIR)
        report_path = resolve_project_path(args.report_out, allowed_root=DEFAULT_OUTPUT_DIR)
        if result_path == report_path:
            raise ValueError("result and report paths must be distinct")
        if result_path != DEFAULT_RESULT.resolve(strict=False):
            raise ValueError("result path must resolve to the fixed result destination")
        if report_path != DEFAULT_REPORT.resolve(strict=False):
            raise ValueError("report path must resolve to the fixed report destination")
        with publication_lock(recovery_dir=DEFAULT_RECOVERY_DIR):
            recover_incomplete_publication(
                result_path=result_path,
                report_path=report_path,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
            payload = build_phase_a_payload(case_path, root=ROOT)
            publish_evidence_pair(
                payload,
                result_path=result_path,
                report_path=report_path,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
    except (EvidencePublicationError, ValueError) as exc:
        print(f"EMOTION-STATE-001 evidence publication failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
