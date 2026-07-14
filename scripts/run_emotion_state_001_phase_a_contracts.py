#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


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
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


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


def main() -> int:
    args = parse_args()
    case_path = resolve_project_path(args.case, allowed_root=DEFAULT_CASE.parent)
    result_path = resolve_project_path(args.out, allowed_root=DEFAULT_OUTPUT_DIR)
    report_path = resolve_project_path(args.report_out, allowed_root=DEFAULT_OUTPUT_DIR)
    if result_path == report_path:
        raise ValueError("result and report paths must be distinct")
    if result_path != DEFAULT_RESULT.resolve(strict=False):
        raise ValueError("result path must resolve to the fixed result destination")
    if report_path != DEFAULT_REPORT.resolve(strict=False):
        raise ValueError("report path must resolve to the fixed report destination")
    payload = build_phase_a_payload(case_path, root=ROOT)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_phase_a_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
