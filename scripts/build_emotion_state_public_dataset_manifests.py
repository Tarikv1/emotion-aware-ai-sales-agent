from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from scripts.emotion_state_public_dataset_contracts import (
    AMI_DATASET_ID,
    CREMA_DATASET_ID,
    SELECTED_PUBLIC_DATASETS,
    _pending_manifest,
    canonical_inventory_bytes,
    inspect_ami_archive,
    safe_extract_ami_archive,
    validate_ami_material,
    validate_crema_material,
    validate_dataset_manifest,
    validate_hash_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATASET_ROOT = Path("data/public/emotion-state")
OUTPUT_DATASET_ROOT = Path("research/sources/emotion_state/datasets")


def _argument_path(value: str | Path, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _guard_public_path(
    value: str | Path,
    *,
    project_root: Path,
    field: str,
    must_exist: bool,
    must_be_directory: bool | None = None,
) -> Path:
    candidate = _argument_path(value, project_root)
    resolved_project_root = project_root.resolve(strict=True)
    private_roots = (
        (resolved_project_root / "data" / "private").resolve(strict=False),
        (resolved_project_root / "data" / "private-restricted").resolve(strict=False),
    )
    unresolved = candidate.resolve(strict=False)
    if any(_is_relative_to(unresolved, private_root) for private_root in private_roots):
        raise ValueError(f"{field} rejects private dataset paths")
    public_root = (resolved_project_root / PUBLIC_DATASET_ROOT).resolve(strict=False)
    if not _is_relative_to(unresolved, public_root):
        raise ValueError(f"{field} must remain under data/public/emotion-state/")
    if must_exist:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"{field} does not exist") from exc
        if not _is_relative_to(resolved, public_root):
            raise ValueError(f"{field} resolves outside data/public/emotion-state/")
    else:
        resolved = unresolved
    if must_be_directory is True and not resolved.is_dir():
        raise ValueError(f"{field} must be a directory")
    if must_be_directory is False and not resolved.is_file():
        raise ValueError(f"{field} must be a file")
    if must_be_directory is None and resolved.exists() and not resolved.is_dir():
        raise ValueError(f"{field} must be a directory when it already exists")
    return resolved


def _guard_output_root(value: str | Path, project_root: Path) -> Path:
    resolved_project_root = project_root.resolve(strict=True)
    candidate = _argument_path(value, resolved_project_root).resolve(strict=False)
    expected = (resolved_project_root / OUTPUT_DATASET_ROOT).resolve(strict=False)
    if candidate != expected:
        raise ValueError(
            "output root must be research/sources/emotion_state/datasets/"
        )
    return candidate


def _canonical_access_date(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("accessed-on must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("accessed-on must be a real YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise ValueError("accessed-on must use canonical YYYY-MM-DD")
    return value


def _validate_quality_inventory(
    payload: Any,
    *,
    dataset_id: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("quality inventory must be an object")
    required = {
        "quality_inventory_version",
        "dataset_id",
        "included_file_count",
        "excluded_file_count",
        "items",
        "limitations",
        "dependency_quarantine",
        "source_metadata",
    }
    if set(payload) != required:
        raise ValueError("quality inventory fields mismatch")
    if type(payload["quality_inventory_version"]) is not int:
        raise ValueError("quality inventory version must be integer 1")
    if payload["quality_inventory_version"] != 1:
        raise ValueError("quality inventory version must be integer 1")
    if payload["dataset_id"] != dataset_id:
        raise ValueError("quality inventory dataset_id mismatch")
    items = payload["items"]
    if not isinstance(items, list):
        raise ValueError("quality inventory items must be a list")
    dispositions = [
        item.get("disposition")
        for item in items
        if isinstance(item, dict)
    ]
    if len(dispositions) != len(items):
        raise ValueError("quality inventory item must be an object")
    included = sum(value == "included" for value in dispositions)
    excluded = sum(value == "excluded" for value in dispositions)
    if included != payload["included_file_count"]:
        raise ValueError("quality inventory included_file_count mismatch")
    if excluded != payload["excluded_file_count"]:
        raise ValueError("quality inventory excluded_file_count mismatch")
    return payload


def _verified_manifest(
    *,
    dataset_id: str,
    accessed_on: str,
    hash_inventory: dict[str, Any],
    hash_inventory_sha256: str,
    quality_inventory: dict[str, Any],
    quality_inventory_sha256: str,
) -> dict[str, Any]:
    manifest = _pending_manifest(dataset_id)
    selected_file_count = hash_inventory["selected_file_count"]
    selected_byte_count = hash_inventory["selected_byte_count"]
    included_file_count = quality_inventory["included_file_count"]
    excluded_file_count = quality_inventory["excluded_file_count"]
    manifest["accessed_on"] = accessed_on
    manifest["completion_status"] = "verified"
    manifest["local_file_hashes"].update({
        "inventory_sha256": hash_inventory_sha256,
        "selected_file_count": selected_file_count,
        "selected_byte_count": selected_byte_count,
    })
    manifest["hash_inventory"].update({
        "inventory_sha256": hash_inventory_sha256,
        "selected_file_count": selected_file_count,
        "selected_byte_count": selected_byte_count,
    })
    manifest["exclusion_inventory"].update({
        "quality_inventory_sha256": quality_inventory_sha256,
        "included_file_count": included_file_count,
        "excluded_file_count": excluded_file_count,
    })
    return validate_dataset_manifest(manifest)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _load_existing_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("existing dataset manifest is unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("existing dataset manifest is not an object")
    return payload


def _atomic_replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def write_dataset_evidence(
    *,
    output_root: Path,
    accessed_on: str,
    materials: Mapping[str, Mapping[str, Any]],
    project_root: Path = ROOT,
) -> list[Path]:
    resolved_project_root = Path(project_root).resolve(strict=True)
    resolved_output_root = _guard_output_root(output_root, resolved_project_root)
    canonical_date = _canonical_access_date(accessed_on)
    if not isinstance(materials, Mapping) or set(materials) != set(
        SELECTED_PUBLIC_DATASETS
    ):
        raise ValueError("materials must contain exactly the selected public datasets")

    artifact_bytes: dict[Path, bytes] = {}
    for dataset_id in SELECTED_PUBLIC_DATASETS:
        material = materials[dataset_id]
        if not isinstance(material, Mapping) or set(material) != {
            "hash_inventory",
            "quality_inventory",
        }:
            raise ValueError("dataset material evidence fields mismatch")
        hash_inventory = material["hash_inventory"]
        quality_inventory = material["quality_inventory"]
        validate_hash_inventory(hash_inventory, resolved_project_root)
        _validate_quality_inventory(quality_inventory, dataset_id=dataset_id)
        hash_bytes = canonical_inventory_bytes(hash_inventory)
        quality_bytes = canonical_inventory_bytes(quality_inventory)
        manifest = _verified_manifest(
            dataset_id=dataset_id,
            accessed_on=canonical_date,
            hash_inventory=hash_inventory,
            hash_inventory_sha256=_sha256_bytes(hash_bytes),
            quality_inventory=quality_inventory,
            quality_inventory_sha256=_sha256_bytes(quality_bytes),
        )
        manifest_bytes = canonical_inventory_bytes(manifest)
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.manifest.json"
        ] = manifest_bytes
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.hashes.json"
        ] = hash_bytes
        artifact_bytes[
            resolved_output_root / f"{dataset_id}.quality.json"
        ] = quality_bytes

    for dataset_id in SELECTED_PUBLIC_DATASETS:
        manifest_path = resolved_output_root / f"{dataset_id}.manifest.json"
        proposed_manifest_bytes = artifact_bytes[manifest_path]
        existing_manifest = _load_existing_manifest(manifest_path)
        if existing_manifest is None:
            continue
        if existing_manifest.get("completion_status") == "verified":
            existing_version = existing_manifest.get("manifest_version")
            proposed_version = json.loads(
                proposed_manifest_bytes.decode("utf-8")
            )["manifest_version"]
            if (
                existing_version == proposed_version
                and manifest_path.read_bytes() != proposed_manifest_bytes
            ):
                raise ValueError("verified_manifest_version_is_immutable")
            if existing_version != proposed_version:
                raise ValueError("verified_manifest_version_is_immutable")
            for suffix in ("hashes", "quality"):
                evidence_path = resolved_output_root / f"{dataset_id}.{suffix}.json"
                if (
                    evidence_path.exists()
                    and evidence_path.read_bytes() != artifact_bytes[evidence_path]
                ):
                    raise ValueError("verified_manifest_version_is_immutable")

    resolved_output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in sorted(artifact_bytes, key=lambda item: item.name):
        payload = artifact_bytes[path]
        if not path.exists() or path.read_bytes() != payload:
            _atomic_replace(path, payload)
        written.append(path)
    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build offline EMOTION-STATE public dataset evidence."
    )
    parser.add_argument("--crema-root")
    parser.add_argument("--ami-archive")
    parser.add_argument("--ami-extract-root")
    parser.add_argument("--accessed-on")
    parser.add_argument(
        "--output-root",
        default=OUTPUT_DATASET_ROOT.as_posix(),
    )
    parser.add_argument(
        "--mode",
        choices=("list-ami", "write-evidence"),
        required=True,
    )
    return parser.parse_args(argv)


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: Path = ROOT,
) -> int:
    try:
        args = parse_args(argv)
        resolved_project_root = Path(project_root).resolve(strict=True)
        if args.ami_archive is None:
            raise ValueError("--ami-archive is required")
        if args.ami_extract_root is None:
            raise ValueError("--ami-extract-root is required")
        ami_archive = _guard_public_path(
            args.ami_archive,
            project_root=resolved_project_root,
            field="ami-archive",
            must_exist=True,
            must_be_directory=False,
        )
        ami_extract_root = _guard_public_path(
            args.ami_extract_root,
            project_root=resolved_project_root,
            field="ami-extract-root",
            must_exist=False,
        )
        if args.mode == "list-ami":
            inspection = inspect_ami_archive(ami_archive, ami_extract_root)
            for member in inspection["members"]:
                print(f"{member['path']}\t{member['classification']}")
            return 0

        if args.crema_root is None:
            raise ValueError("--crema-root is required for write-evidence")
        if args.accessed_on is None:
            raise ValueError("--accessed-on is required for write-evidence")
        crema_root = _guard_public_path(
            args.crema_root,
            project_root=resolved_project_root,
            field="crema-root",
            must_exist=True,
            must_be_directory=True,
        )
        output_root = _guard_output_root(args.output_root, resolved_project_root)
        accessed_on = _canonical_access_date(args.accessed_on)
        extraction = safe_extract_ami_archive(ami_archive, ami_extract_root)
        materials = {
            CREMA_DATASET_ID: validate_crema_material(
                crema_root,
                project_root=resolved_project_root,
            ),
            AMI_DATASET_ID: validate_ami_material(
                ami_extract_root,
                archive_path=ami_archive,
                extraction=extraction,
                project_root=resolved_project_root,
            ),
        }
        write_dataset_evidence(
            output_root=output_root,
            accessed_on=accessed_on,
            materials=materials,
            project_root=resolved_project_root,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"offline dataset verifier failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
